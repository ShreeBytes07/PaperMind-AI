import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.HttpExchange;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.sql.*;
import java.time.Duration;
import java.util.*;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

public class Main {

    private static final String DB_HOST =
            System.getenv().getOrDefault("DB_HOST", "localhost");

    private static final String DB_PORT =
            System.getenv().getOrDefault("DB_PORT", "3306");

    private static final String DB_NAME =
            System.getenv().getOrDefault("DB_NAME", "papermind_ai");

    private static final String DB_USER =
            System.getenv().getOrDefault("DB_USER", "root");

    private static final String DB_PASSWORD =
            System.getenv("DB_PASSWORD");

    private static final int MAX_REQUEST_SIZE = 5 * 1024 * 1024;

    private static final HttpClient HTTP_CLIENT =
            HttpClient.newBuilder()
                    .connectTimeout(Duration.ofSeconds(5))
                    .build();

    // =========================================================
    // DATABASE
    // =========================================================

    private static Connection getConnection() throws SQLException {

        if (DB_PASSWORD == null || DB_PASSWORD.isBlank()) {
            throw new SQLException(
                    "DB_PASSWORD is not set in this terminal.");
        }

        String url = "jdbc:mysql://" + DB_HOST + ":" +
                DB_PORT + "/" + DB_NAME;

        return DriverManager.getConnection(
                url, DB_USER, DB_PASSWORD);
    }

    // =========================================================
    // JSON RESPONSE AND CORS
    // =========================================================

    private static void sendJson(
            HttpExchange exchange,
            int status,
            String json) throws IOException {

        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);

        exchange.getResponseHeaders().set(
                "Content-Type", "application/json; charset=UTF-8");

        exchange.getResponseHeaders().set(
                "Cache-Control", "no-store");

        exchange.getResponseHeaders().set(
                "Access-Control-Allow-Origin", "*");

        exchange.getResponseHeaders().set(
                "Access-Control-Allow-Methods", "GET, POST, OPTIONS");

        exchange.getResponseHeaders().set(
                "Access-Control-Allow-Headers", "Content-Type");

        exchange.sendResponseHeaders(status, bytes.length);

        try (OutputStream output = exchange.getResponseBody()) {
            output.write(bytes);
        }
    }

    private static boolean handleOptions(
            HttpExchange exchange) throws IOException {

        if ("OPTIONS".equalsIgnoreCase(
                exchange.getRequestMethod())) {

            exchange.getResponseHeaders().set(
                    "Access-Control-Allow-Origin", "*");

            exchange.getResponseHeaders().set(
                    "Access-Control-Allow-Methods",
                    "GET, POST, OPTIONS");

            exchange.getResponseHeaders().set(
                    "Access-Control-Allow-Headers", "Content-Type");

            exchange.sendResponseHeaders(204, -1);
            exchange.close();

            return true;
        }

        return false;
    }

    private static String escapeJson(String value) {

        if (value == null) {
            return "";
        }

        StringBuilder output = new StringBuilder();

        for (int i = 0; i < value.length(); i++) {

            char c = value.charAt(i);

            switch (c) {
                case '"':
                    output.append("\\\"");
                    break;

                case '\\':
                    output.append("\\\\");
                    break;

                case '\b':
                    output.append("\\b");
                    break;

                case '\f':
                    output.append("\\f");
                    break;

                case '\n':
                    output.append("\\n");
                    break;

                case '\r':
                    output.append("\\r");
                    break;

                case '\t':
                    output.append("\\t");
                    break;

                default:
                    if (c < 0x20) {
                        output.append(String.format(
                                "\\u%04x", (int) c));
                    } else {
                        output.append(c);
                    }
            }
        }

        return output.toString();
    }

    private static String nullableJson(String value) {

        if (value == null) {
            return "null";
        }

        return "\"" + escapeJson(value) + "\"";
    }

    // =========================================================
    // JSON VALUE SERIALIZATION
    // =========================================================

    private static String jsonValue(Object value) {

        if (value == null) {
            return "null";
        }

        if (value instanceof String) {
            return "\"" + escapeJson((String) value) + "\"";
        }

        if (value instanceof Number || value instanceof Boolean) {
            return value.toString();
        }

        if (value instanceof Map<?, ?>) {

            StringBuilder output = new StringBuilder("{");
            boolean first = true;

            for (Map.Entry<?, ?> entry :
                    ((Map<?, ?>) value).entrySet()) {

                if (!first) {
                    output.append(",");
                }

                output.append(nullableJson(
                        String.valueOf(entry.getKey())));

                output.append(":");
                output.append(jsonValue(entry.getValue()));

                first = false;
            }

            return output.append("}").toString();
        }

        if (value instanceof List<?>) {

            StringBuilder output = new StringBuilder("[");
            boolean first = true;

            for (Object item : (List<?>) value) {

                if (!first) {
                    output.append(",");
                }

                output.append(jsonValue(item));
                first = false;
            }

            return output.append("]").toString();
        }

        return nullableJson(value.toString());
    }

    // =========================================================
    // REQUEST BODY
    // =========================================================

    private static String readRequestBody(
            HttpExchange exchange) throws IOException {

        String contentLength = exchange.getRequestHeaders()
                .getFirst("Content-Length");

        if (contentLength == null) {
            throw new IllegalArgumentException(
                    "Content-Length header is required.");
        }

        long length;

        try {
            length = Long.parseLong(contentLength);
        } catch (NumberFormatException e) {
            throw new IllegalArgumentException(
                    "Invalid Content-Length.");
        }

        if (length <= 0 || length > MAX_REQUEST_SIZE) {
            throw new IllegalArgumentException(
                    "Request body must be between 1 byte and 5 MB.");
        }

        byte[] body;

        try (var input = exchange.getRequestBody()) {
            body = input.readNBytes((int) length + 1);
        }

        if (body.length != length) {
            throw new IllegalArgumentException(
                    "Request body length mismatch.");
        }

        return new String(body, StandardCharsets.UTF_8);
    }

    private static Map<String, Object> readJsonObject(
            HttpExchange exchange) throws IOException {

        Object parsed = parseJson(readRequestBody(exchange));

        if (!(parsed instanceof Map<?, ?>)) {
            throw new IllegalArgumentException(
                    "A JSON object is required.");
        }

        @SuppressWarnings("unchecked")
        Map<String, Object> result =
                (Map<String, Object>) parsed;

        return result;
    }

    private static String jsonField(
            Map<String, Object> data, String field) {

        Object value = data.get(field);

        if (value == null) {
            return null;
        }

        if (!(value instanceof String)) {
            throw new IllegalArgumentException(
                    "Field '" + field + "' must be a string.");
        }

        return (String) value;
    }

    private static String requiredField(
            Map<String, Object> data, String field) {

        String value = jsonField(data, field);

        if (value == null || value.isBlank()) {
            throw new IllegalArgumentException(
                    "Field '" + field + "' is required.");
        }

        return value.trim();
    }

    private static long parsePaperId(String path) {

        String prefix = "/api/papers/";

        if (!path.startsWith(prefix)) {
            throw new IllegalArgumentException("Invalid paper URL.");
        }

        String remaining = path.substring(prefix.length());

        if (remaining.isBlank() || remaining.contains("/")) {
            throw new IllegalArgumentException("Invalid paper ID.");
        }

        try {
            long id = Long.parseLong(remaining);

            if (id <= 0) {
                throw new IllegalArgumentException("Invalid paper ID.");
            }

            return id;

        } catch (NumberFormatException e) {
            throw new IllegalArgumentException("Invalid paper ID.");
        }
    }

    // =========================================================
    // HEALTH API
    // GET /health
    // =========================================================

    private static void handleHealth(HttpExchange exchange)
            throws IOException {

        if (handleOptions(exchange)) {
            return;
        }

        if (!"GET".equalsIgnoreCase(
                exchange.getRequestMethod())) {

            sendJson(exchange, 405,
                    "{\"error\":\"Method not allowed\"}");
            return;
        }

        sendJson(exchange, 200,
                "{\"status\":\"ok\"," +
                "\"service\":\"PaperMind AI Backend\"}");
    }

    // =========================================================
    // SYLLABUS TOPICS
    // GET /api/topics
    // =========================================================

    private static void handleTopics(HttpExchange exchange)
            throws IOException {

        if (handleOptions(exchange)) {
            return;
        }

        if (!"GET".equalsIgnoreCase(
                exchange.getRequestMethod())) {

            sendJson(exchange, 405,
                    "{\"error\":\"Method not allowed\"}");
            return;
        }

        StringBuilder json =
                new StringBuilder("{\"topics\":[");

        try (Connection connection = getConnection();
             PreparedStatement ps = connection.prepareStatement(
                     "SELECT id, topic_name FROM syllabus_topics " +
                     "ORDER BY id");
             ResultSet rs = ps.executeQuery()) {

            boolean first = true;

            while (rs.next()) {

                if (!first) {
                    json.append(",");
                }

                json.append("{")
                    .append("\"id\":").append(rs.getInt("id"))
                    .append(",\"topic_name\":")
                    .append(nullableJson(
                            rs.getString("topic_name")))
                    .append("}");

                first = false;
            }

            json.append("]}");

            sendJson(exchange, 200, json.toString());

        } catch (SQLException e) {

            System.err.println(
                    "Topics query failed: " + e.getMessage());

            sendJson(exchange, 500,
                    "{\"error\":\"Unable to fetch topics\"}");
        }
    }

    // =========================================================
    // SINGLE QUESTION ANALYSIS
    // POST /api/analyze
    // =========================================================

    private static void handleAnalyze(HttpExchange exchange)
            throws IOException {

        if (handleOptions(exchange)) {
            return;
        }

        if (!"POST".equalsIgnoreCase(
                exchange.getRequestMethod())) {

            sendJson(exchange, 405,
                    "{\"error\":\"Method not allowed\"}");
            return;
        }

        try {
            Map<String, Object> data =
                    readJsonObject(exchange);

            String question = requiredField(data, "question");

            String requestJson =
                    "{\"question\":\"" +
                    escapeJson(question) + "\"}";

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(
                            "http://127.0.0.1:5000/analyze"))
                    .timeout(Duration.ofSeconds(30))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(
                            requestJson, StandardCharsets.UTF_8))
                    .build();

            HttpResponse<String> response = HTTP_CLIENT.send(
                    request,
                    HttpResponse.BodyHandlers.ofString(
                            StandardCharsets.UTF_8));

            // Ensure response is valid JSON.
            parseJson(response.body());

            sendJson(exchange, response.statusCode(),
                    response.body());

        } catch (InterruptedException e) {

            Thread.currentThread().interrupt();

            sendJson(exchange, 503,
                    "{\"error\":\"Analysis interrupted\"}");

        } catch (IllegalArgumentException e) {

            sendJson(exchange, 400,
                    "{\"error\":\"" +
                    escapeJson(e.getMessage()) + "\"}");

        } catch (IOException e) {

            System.err.println(
                    "Python analysis request failed: " +
                    e.getMessage());

            sendJson(exchange, 502,
                    "{\"error\":\"Unable to contact Python ML service\"}");
        }
    }

    // =========================================================
    // PAPER LIST AND CREATE
    // GET /api/papers
    // POST /api/papers
    // =========================================================

    private static void handlePapers(HttpExchange exchange)
            throws IOException {

        if (handleOptions(exchange)) {
            return;
        }

        String method = exchange.getRequestMethod();

        if ("GET".equalsIgnoreCase(method)) {
            listPapers(exchange);

        } else if ("POST".equalsIgnoreCase(method)) {
            createPaper(exchange);

        } else {
            sendJson(exchange, 405,
                    "{\"error\":\"Method not allowed\"}");
        }
    }

    private static void listPapers(HttpExchange exchange)
            throws IOException {

        String sql =
                "SELECT id, paper_name, subject, original_filename, " +
                "mime_type, processing_status, total_questions, " +
                "created_at, updated_at " +
                "FROM question_papers ORDER BY created_at DESC";

        StringBuilder json =
                new StringBuilder("{\"papers\":[");

        try (Connection connection = getConnection();
             PreparedStatement ps =
                     connection.prepareStatement(sql);
             ResultSet rs = ps.executeQuery()) {

            boolean first = true;

            while (rs.next()) {

                if (!first) {
                    json.append(",");
                }

                json.append("{")
                    .append("\"id\":").append(rs.getLong("id"))
                    .append(",\"paper_name\":")
                    .append(nullableJson(rs.getString("paper_name")))
                    .append(",\"subject\":")
                    .append(nullableJson(rs.getString("subject")))
                    .append(",\"original_filename\":")
                    .append(nullableJson(
                            rs.getString("original_filename")))
                    .append(",\"mime_type\":")
                    .append(nullableJson(rs.getString("mime_type")))
                    .append(",\"processing_status\":")
                    .append(nullableJson(
                            rs.getString("processing_status")))
                    .append(",\"total_questions\":")
                    .append(rs.getInt("total_questions"))
                    .append(",\"created_at\":")
                    .append(nullableJson(rs.getString("created_at")))
                    .append(",\"updated_at\":")
                    .append(nullableJson(rs.getString("updated_at")))
                    .append("}");

                first = false;
            }

            json.append("]}");

            sendJson(exchange, 200, json.toString());

        } catch (SQLException e) {

            System.err.println(
                    "Paper list query failed: " + e.getMessage());

            sendJson(exchange, 500,
                    "{\"error\":\"Unable to fetch papers\"}");
        }
    }

    private static void createPaper(HttpExchange exchange)
            throws IOException {

        try {
            Map<String, Object> data =
                    readJsonObject(exchange);

            String paperName =
                    requiredField(data, "paper_name");

            String subject = jsonField(data, "subject");
            String filename =
                    jsonField(data, "original_filename");
            String mimeType = jsonField(data, "mime_type");
            String storedPath =
                    jsonField(data, "stored_file_path");
            String extractedText =
                    jsonField(data, "extracted_text");

            String sql =
                    "INSERT INTO question_papers " +
                    "(paper_name, subject, original_filename, mime_type, " +
                    "stored_file_path, extracted_text, processing_status, " +
                    "total_questions) VALUES (?, ?, ?, ?, ?, ?, ?, 0)";

            try (Connection connection = getConnection();
                 PreparedStatement ps = connection.prepareStatement(
                         sql, Statement.RETURN_GENERATED_KEYS)) {

                ps.setString(1, paperName);
                ps.setString(2, subject);
                ps.setString(3, filename);
                ps.setString(4, mimeType);
                ps.setString(5, storedPath);
                ps.setString(6, extractedText);
                ps.setString(7, "SAVED");

                ps.executeUpdate();

                try (ResultSet keys = ps.getGeneratedKeys()) {

                    if (!keys.next()) {
                        sendJson(exchange, 500,
                                "{\"error\":\"Paper ID unavailable\"}");
                        return;
                    }

                    long id = keys.getLong(1);

                    sendJson(exchange, 201,
                            "{\"message\":\"Paper saved successfully\"," +
                            "\"id\":" + id +
                            ",\"paper_name\":" +
                            nullableJson(paperName) +
                            ",\"processing_status\":\"SAVED\"}");
                }
            }

        } catch (IllegalArgumentException e) {

            sendJson(exchange, 400,
                    "{\"error\":\"" +
                    escapeJson(e.getMessage()) + "\"}");

        } catch (SQLException e) {

            System.err.println(
                    "Paper creation failed: " + e.getMessage());

            sendJson(exchange, 500,
                    "{\"error\":\"Unable to save paper\"}");
        }
    }

    // =========================================================
    // =========================================================
    // EXTRACT QUESTIONS
    // POST /api/papers/{id}/extract
    // Uses Python extraction API
    // =========================================================

    private static void handleExtractQuestions(
            HttpExchange exchange, long paperId)
            throws IOException {

        String extractedText;

        try (Connection connection = getConnection();
             PreparedStatement ps = connection.prepareStatement(
                     "SELECT extracted_text FROM question_papers WHERE id = ?")) {

            ps.setLong(1, paperId);

            try (ResultSet rs = ps.executeQuery()) {
                if (!rs.next()) {
                    sendJson(exchange, 404,
                            "{\"error\":\"Paper not found\"}");
                    return;
                }
                extractedText = rs.getString("extracted_text");
            }

        } catch (SQLException e) {
            System.err.println("Paper text query failed: " + e.getMessage());
            sendJson(exchange, 500,
                    "{\"error\":\"Unable to load paper text\"}");
            return;
        }

        if (extractedText == null || extractedText.isBlank()) {
            sendJson(exchange, 400,
                    "{\"error\":\"No extracted text available\"}");
            return;
        }

        String pythonResponse;

        try {
            String requestJson =
                    "{\"text\":" + nullableJson(extractedText) + "}";

            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create("http://127.0.0.1:5000/extract"))
                    .timeout(Duration.ofSeconds(60))
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(
                            requestJson, StandardCharsets.UTF_8))
                    .build();

            HttpResponse<String> response = HTTP_CLIENT.send(
                    request,
                    HttpResponse.BodyHandlers.ofString(
                            StandardCharsets.UTF_8));

            if (response.statusCode() < 200 ||
                    response.statusCode() >= 300) {
                sendJson(exchange, 502,
                        "{\"error\":\"Python extraction service failed\"}");
                return;
            }

            pythonResponse = response.body();

        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            sendJson(exchange, 503,
                    "{\"error\":\"Extraction request was interrupted\"}");
            return;

        } catch (IOException e) {
            System.err.println("Python API error: " + e.getMessage());
            sendJson(exchange, 503,
                    "{\"error\":\"Python extraction service is unavailable\"}");
            return;
        }

        Map<String, Object> extractionResult;

        try {
            Object parsed = parseJson(pythonResponse);

            if (!(parsed instanceof Map<?, ?>)) {
                sendJson(exchange, 502,
                        "{\"error\":\"Invalid Python response\"}");
                return;
            }

            @SuppressWarnings("unchecked")
            Map<String, Object> result =
                    (Map<String, Object>) parsed;

            extractionResult = result;

        } catch (RuntimeException e) {
            sendJson(exchange, 502,
                    "{\"error\":\"Unable to parse extraction response\"}");
            return;
        }

        String status = String.valueOf(
                extractionResult.get("status"));

        String method = String.valueOf(
                extractionResult.get("method"));

        String message = String.valueOf(
                extractionResult.get("message"));

        Object rawQuestions = extractionResult.get("questions");

        if (!"extracted".equals(status) &&
                !"extracted_with_review".equals(status)) {

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("status", status);
            result.put("message", message);
            result.put("total_questions", 0);
            result.put("questions", Collections.emptyList());

            sendJson(exchange, 422, jsonValue(result));
            return;
        }

        if (!(rawQuestions instanceof List<?>)) {
            sendJson(exchange, 502,
                    "{\"error\":\"Invalid questions data from Python\"}");
            return;
        }

        List<?> extractedQuestions = (List<?>) rawQuestions;

        if (extractedQuestions.isEmpty()) {
            sendJson(exchange, 422,
                    "{\"error\":\"No questions were extracted\"}");
            return;
        }

        List<Map<String, String>> questions = new ArrayList<>();

        for (Object item : extractedQuestions) {
            if (!(item instanceof Map<?, ?>)) {
                sendJson(exchange, 502,
                        "{\"error\":\"Invalid question entry\"}");
                return;
            }

            Map<?, ?> question = (Map<?, ?>) item;

            Object numberValue = question.get("question_number");
            Object textValue = question.get("question_text");

            if (numberValue == null || textValue == null) {
                sendJson(exchange, 502,
                        "{\"error\":\"Question number or text is missing\"}");
                return;
            }

            String number = String.valueOf(numberValue);
            String questionText = String.valueOf(textValue).trim();

            if (questionText.isBlank()) {
                sendJson(exchange, 502,
                        "{\"error\":\"An extracted question is empty\"}");
                return;
            }

            Map<String, String> validatedQuestion =
                    new LinkedHashMap<>();

            validatedQuestion.put("question_number", number);
            validatedQuestion.put("question_text", questionText);
            questions.add(validatedQuestion);
        }

        try (Connection connection = getConnection()) {
            connection.setAutoCommit(false);

            try {
                // Preserve all existing question records
                try (PreparedStatement check =
                             connection.prepareStatement(
                                     "SELECT COUNT(*) FROM extracted_questions WHERE paper_id = ?")) {

                    check.setLong(1, paperId);

                    try (ResultSet rs = check.executeQuery()) {
                        if (rs.next() && rs.getInt(1) > 0) {
                            connection.rollback();
                            sendJson(exchange, 409,
                                    "{\"error\":\"Questions already exist. Existing records were preserved.\"}");
                            return;
                        }
                    }
                }

                String insertSql =
                        "INSERT INTO extracted_questions " +
                        "(paper_id, question_number, question_text, extraction_method) " +
                        "VALUES (?, ?, ?, ?)";

                try (PreparedStatement insert =
                             connection.prepareStatement(insertSql)) {

                    for (Map<String, String> question : questions) {
                        insert.setLong(1, paperId);
                        insert.setString(2,
                                question.get("question_number"));
                        insert.setString(3,
                                question.get("question_text"));
                        insert.setString(4, "PYTHON");
                        insert.addBatch();
                    }

                    insert.executeBatch();
                }

                try (PreparedStatement update =
                             connection.prepareStatement(
                                     "UPDATE question_papers " +
                                     "SET total_questions = ?, " +
                                     "processing_status = 'EXTRACTED' " +
                                     "WHERE id = ?")) {

                    update.setInt(1, questions.size());
                    update.setLong(2, paperId);

                    if (update.executeUpdate() != 1) {
                        throw new SQLException("Paper not found.");
                    }
                }

                connection.commit();

            } catch (SQLException e) {
                connection.rollback();
                throw e;

            } finally {
                connection.setAutoCommit(true);
            }

            Map<String, Object> result = new LinkedHashMap<>();
            result.put("paper_id", paperId);
            result.put("status", status);
            result.put("method", method);
            result.put("confidence",
                    extractionResult.get("confidence"));
            result.put("total_questions", questions.size());
            result.put("message", message);
            result.put("questions", questions);

            sendJson(exchange, 200, jsonValue(result));

        } catch (SQLException e) {
            System.err.println(
                    "Question extraction database error: " + e.getMessage());

            sendJson(exchange, 500,
                    "{\"error\":\"Unable to save extracted questions\"}");
        }
    }
    // ANALYZE ALL QUESTIONS IN A PAPER
    // POST /api/papers/{id}/analyze
    // =========================================================

    private static void handleAnalyzePaper(
            HttpExchange exchange, long paperId)
            throws IOException {

        List<Map<String, Object>> questions = new ArrayList<>();

        // Load extracted questions.

        try (Connection connection = getConnection();
             PreparedStatement ps = connection.prepareStatement(
                     "SELECT id, question_text FROM extracted_questions " +
                     "WHERE paper_id = ? ORDER BY id")) {

            ps.setLong(1, paperId);

            try (ResultSet rs = ps.executeQuery()) {

                while (rs.next()) {

                    Map<String, Object> question =
                            new LinkedHashMap<>();

                    question.put("id", rs.getLong("id"));
                    question.put("question_text",
                            rs.getString("question_text"));

                    questions.add(question);
                }
            }

        } catch (SQLException e) {

            System.err.println(
                    "Question query failed: " + e.getMessage());

            sendJson(exchange, 500,
                    "{\"error\":\"Unable to load questions\"}");
            return;
        }

        if (questions.isEmpty()) {
            sendJson(exchange, 400,
                    "{\"error\":\"No extracted questions found\"}");
            return;
        }

        int saved = 0;
        int skipped = 0;
        List<String> errors = new ArrayList<>();
        List<Map<String, Object>> results = new ArrayList<>();
        List<Map<String, Object>> skippedQuestions = new ArrayList<>();

        for (Map<String, Object> question : questions) {

            long questionId = (Long) question.get("id");
            String questionText =
                    (String) question.get("question_text");

            try {
                String requestJson =
                        "{\"question\":\"" +
                        escapeJson(questionText) + "\"}";

                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(
                                "http://127.0.0.1:5000/analyze"))
                        .timeout(Duration.ofSeconds(30))
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(
                                requestJson, StandardCharsets.UTF_8))
                        .build();

                HttpResponse<String> response = HTTP_CLIENT.send(
                        request,
                        HttpResponse.BodyHandlers.ofString(
                                StandardCharsets.UTF_8));

                if (response.statusCode() < 200 ||
                        response.statusCode() >= 300) {

                    errors.add("Question " + questionId +
                            ": Python API HTTP " +
                            response.statusCode());

                    continue;
                }

                Object parsed = parseJson(response.body());

                if (!(parsed instanceof Map<?, ?>)) {
                    errors.add("Question " + questionId +
                            ": Invalid Python response");
                    continue;
                }

                @SuppressWarnings("unchecked")
                Map<String, Object> analysis =
                        (Map<String, Object>) parsed;

                String analysisStatus =
                        stringValue(analysis.get("status"));

                if (!"analyzed".equalsIgnoreCase(analysisStatus)) {

                    Map<String, Object> skippedItem =
                            new LinkedHashMap<>();

                    skippedItem.put("question_id", questionId);
                    skippedItem.put("question", questionText);
                    skippedItem.put("subject",
                            analysis.get("subject"));
                    skippedItem.put("status", "skipped");
                    skippedItem.put("reason",
                            analysis.get("reason"));

                    skippedQuestions.add(skippedItem);
                    skipped++;
                    continue;
                }

                String mainConcept =
                        stringValue(analysis.get("main_concept"));

                String supporting =
                        stringValue(analysis.get("supporting_concepts"));

                String difficulty =
                        stringValue(analysis.get("difficulty"));

                String bloom =
                        stringValue(analysis.get("bloom"));

                String marks =
                        stringValue(analysis.get("suggested_marks"));

                String explanation =
                        stringValue(analysis.get("analysis_explanation"));

                String detectedConcepts =
                        jsonValue(analysis.get("detected_concepts"));

                String scoreBreakdown =
                        jsonValue(analysis.get("score_breakdown"));

                Object scoreObject = analysis.get("score");

                java.math.BigDecimal difficultyScore = null;

                if (scoreObject != null) {
                    try {
                        difficultyScore =
                                new java.math.BigDecimal(
                                        scoreObject.toString());
                    } catch (NumberFormatException ignored) {
                        // Leave the score null if it is not numeric.
                    }
                }

                // Insert one analysis record per question.
                // Existing records are retained as history.

                String insertSql =
                        "INSERT INTO question_analysis " +
                        "(question_id, main_concept, supporting_concepts, " +
                        "detected_concepts, difficulty, difficulty_score, " +
                        "bloom_level, suggested_marks, score_breakdown, " +
                        "analysis_explanation, model_version) " +
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)";

                try (Connection connection = getConnection();
                     PreparedStatement ps =
                             connection.prepareStatement(insertSql)) {

                    ps.setLong(1, questionId);
                    ps.setString(2, mainConcept);
                    ps.setString(3, supporting);

                    if (detectedConcepts == null) {
                        ps.setNull(4, Types.VARCHAR);
                    } else {
                        ps.setString(4, detectedConcepts);
                    }

                    ps.setString(5, difficulty);

                    if (difficultyScore == null) {
                        ps.setNull(6, Types.DECIMAL);
                    } else {
                        ps.setBigDecimal(6, difficultyScore);
                    }

                    ps.setString(7, bloom);
                    ps.setString(8, marks);

                    if (scoreBreakdown == null) {
                        ps.setNull(9, Types.VARCHAR);
                    } else {
                        ps.setString(9, scoreBreakdown);
                    }

                    ps.setString(10, explanation);
                    ps.setString(11, "PaperMind-Heuristic-v1");

                    ps.executeUpdate();
                }

                Map<String, Object> result =
                        new LinkedHashMap<>();

                result.put("question_id", questionId);
                result.put("main_concept", mainConcept);
                result.put("difficulty", difficulty);
                result.put("bloom_level", bloom);
                result.put("suggested_marks", marks);
                result.put("score", scoreObject);

                results.add(result);
                saved++;

            } catch (InterruptedException e) {

                Thread.currentThread().interrupt();

                sendJson(exchange, 503,
                        "{\"error\":\"Analysis interrupted\"}");
                return;

            } catch (Exception e) {

                System.err.println(
                        "Question analysis failed for ID " +
                        questionId + ": " + e.getMessage());

                errors.add("Question " + questionId +
                        ": Analysis or database save failed");
            }
        }

        Map<String, Object> response =
                new LinkedHashMap<>();

        response.put("paper_id", paperId);
        response.put("total_questions", questions.size());
        response.put("analyzed_count", saved);
        response.put("skipped_count", skipped);
        response.put("saved_analyses", saved);
        response.put("results", results);
        response.put("skipped_questions", skippedQuestions);
        response.put("errors", errors);

        int status = errors.isEmpty() ? 200 : 207;

        sendJson(exchange, status, jsonValue(response));
    }

    private static String stringValue(Object value) {

        if (value == null) {
            return null;
        }

        return value instanceof String
                ? (String) value
                : value.toString();
    }

    // =========================================================
    // GET SAVED ANALYSIS
    // GET /api/questions/{id}/analysis
    // =========================================================

    private static void handleQuestionAnalysis(
            HttpExchange exchange) throws IOException {

        if (handleOptions(exchange)) {
            return;
        }

        if (!"GET".equalsIgnoreCase(
                exchange.getRequestMethod())) {

            sendJson(exchange, 405,
                    "{\"error\":\"Method not allowed\"}");
            return;
        }

        String path = exchange.getRequestURI().getPath();
        String prefix = "/api/questions/";
        String suffix = "/analysis";

        if (!path.startsWith(prefix) || !path.endsWith(suffix)) {
            sendJson(exchange, 400,
                    "{\"error\":\"Invalid analysis URL\"}");
            return;
        }

        String idText = path.substring(
                prefix.length(), path.length() - suffix.length());

        long questionId;

        try {
            questionId = Long.parseLong(idText);

            if (questionId <= 0) {
                throw new NumberFormatException();
            }

        } catch (NumberFormatException e) {
            sendJson(exchange, 400,
                    "{\"error\":\"Invalid question ID\"}");
            return;
        }

        String sql =
                "SELECT id, question_id, main_concept, " +
                "supporting_concepts, detected_concepts, difficulty, " +
                "difficulty_score, bloom_level, suggested_marks, " +
                "score_breakdown, analysis_explanation, model_version, " +
                "created_at FROM question_analysis " +
                "WHERE question_id = ? ORDER BY created_at DESC, id DESC";

        StringBuilder json =
                new StringBuilder("{\"question_id\":" +
                questionId + ",\"analyses\":[");

        try (Connection connection = getConnection();
             PreparedStatement ps = connection.prepareStatement(sql)) {

            ps.setLong(1, questionId);

            try (ResultSet rs = ps.executeQuery()) {

                boolean first = true;

                while (rs.next()) {

                    if (!first) {
                        json.append(",");
                    }

                    json.append("{")
                        .append("\"id\":").append(rs.getLong("id"))
                        .append(",\"question_id\":")
                        .append(rs.getLong("question_id"))
                        .append(",\"main_concept\":")
                        .append(nullableJson(
                                rs.getString("main_concept")))
                        .append(",\"supporting_concepts\":")
                        .append(nullableJson(
                                rs.getString("supporting_concepts")))
                        .append(",\"detected_concepts\":")
                        .append(jsonColumn(
                                rs.getString("detected_concepts")))
                        .append(",\"difficulty\":")
                        .append(nullableJson(
                                rs.getString("difficulty")))
                        .append(",\"difficulty_score\":")
                        .append(nullableJson(
                                rs.getString("difficulty_score")))
                        .append(",\"bloom_level\":")
                        .append(nullableJson(
                                rs.getString("bloom_level")))
                        .append(",\"suggested_marks\":")
                        .append(nullableJson(
                                rs.getString("suggested_marks")))
                        .append(",\"score_breakdown\":")
                        .append(jsonColumn(
                                rs.getString("score_breakdown")))
                        .append(",\"analysis_explanation\":")
                        .append(nullableJson(
                                rs.getString("analysis_explanation")))
                        .append(",\"model_version\":")
                        .append(nullableJson(
                                rs.getString("model_version")))
                        .append(",\"created_at\":")
                        .append(nullableJson(
                                rs.getString("created_at")))
                        .append("}");

                    first = false;
                }
            }

            json.append("]}");

            sendJson(exchange, 200, json.toString());

        } catch (SQLException e) {

            System.err.println(
                    "Analysis retrieval failed: " + e.getMessage());

            sendJson(exchange, 500,
                    "{\"error\":\"Unable to retrieve analysis\"}");
        }
    }

    private static String jsonColumn(String value) {

        if (value == null) {
            return "null";
        }

        try {
            parseJson(value);
            return value;
        } catch (IllegalArgumentException e) {
            return nullableJson(value);
        }
    }

    // =========================================================
    // PAPER DETAILS
    // GET /api/papers/{id}
    // POST /api/papers/{id}/extract
    // POST /api/papers/{id}/analyze
    // =========================================================

    private static void handlePaperDetails(
            HttpExchange exchange) throws IOException {

        if (handleOptions(exchange)) {
            return;
        }

        String path = exchange.getRequestURI().getPath();
        String method = exchange.getRequestMethod();

        // Extract questions route.

        if (path.endsWith("/extract")) {

            if (!"POST".equalsIgnoreCase(method)) {
                sendJson(exchange, 405,
                        "{\"error\":\"Method not allowed\"}");
                return;
            }

            String idPath = path.substring(
                    0, path.length() - "/extract".length());

            try {
                long id = parsePaperId(idPath);
                handleExtractQuestions(exchange, id);

            } catch (IllegalArgumentException e) {
                sendJson(exchange, 400,
                        "{\"error\":\"Invalid paper ID\"}");
            }

            return;
        }

        // Analyze all questions route.

        if (path.endsWith("/analyze")) {

            if (!"POST".equalsIgnoreCase(method)) {
                sendJson(exchange, 405,
                        "{\"error\":\"Method not allowed\"}");
                return;
            }

            String idPath = path.substring(
                    0, path.length() - "/analyze".length());

            try {
                long id = parsePaperId(idPath);
                handleAnalyzePaper(exchange, id);

            } catch (IllegalArgumentException e) {
                sendJson(exchange, 400,
                        "{\"error\":\"Invalid paper ID\"}");
            }

            return;
        }

        // Paper details route.

        if (!"GET".equalsIgnoreCase(method)) {
            sendJson(exchange, 405,
                    "{\"error\":\"Method not allowed\"}");
            return;
        }

        final long paperId;

        try {
            paperId = parsePaperId(path);

        } catch (IllegalArgumentException e) {
            sendJson(exchange, 400,
                    "{\"error\":\"Invalid paper ID\"}");
            return;
        }

        String paperSql =
                "SELECT id, paper_name, subject, original_filename, " +
                "mime_type, stored_file_path, extracted_text, " +
                "processing_status, total_questions, created_at, updated_at " +
                "FROM question_papers WHERE id = ?";

        try (Connection connection = getConnection();
             PreparedStatement ps =
                     connection.prepareStatement(paperSql)) {

            ps.setLong(1, paperId);

            try (ResultSet rs = ps.executeQuery()) {

                if (!rs.next()) {
                    sendJson(exchange, 404,
                            "{\"error\":\"Paper not found\"}");
                    return;
                }

                StringBuilder json =
                        new StringBuilder("{\"paper\":{");

                json.append("\"id\":")
                    .append(rs.getLong("id"))
                    .append(",\"paper_name\":")
                    .append(nullableJson(rs.getString("paper_name")))
                    .append(",\"subject\":")
                    .append(nullableJson(rs.getString("subject")))
                    .append(",\"original_filename\":")
                    .append(nullableJson(
                            rs.getString("original_filename")))
                    .append(",\"mime_type\":")
                    .append(nullableJson(rs.getString("mime_type")))
                    .append(",\"stored_file_path\":")
                    .append(nullableJson(
                            rs.getString("stored_file_path")))
                    .append(",\"extracted_text\":")
                    .append(nullableJson(
                            rs.getString("extracted_text")))
                    .append(",\"processing_status\":")
                    .append(nullableJson(
                            rs.getString("processing_status")))
                    .append(",\"total_questions\":")
                    .append(rs.getInt("total_questions"))
                    .append(",\"created_at\":")
                    .append(nullableJson(rs.getString("created_at")))
                    .append(",\"updated_at\":")
                    .append(nullableJson(rs.getString("updated_at")))
                    .append("},\"questions\":[");

                String questionSql =
                        "SELECT id, question_number, question_text, " +
                        "suggested_marks FROM extracted_questions " +
                        "WHERE paper_id = ? " +
                        "ORDER BY CAST(question_number AS UNSIGNED), id";

                try (PreparedStatement qps =
                             connection.prepareStatement(questionSql)) {

                    qps.setLong(1, paperId);

                    try (ResultSet qrs = qps.executeQuery()) {

                        boolean first = true;

                        while (qrs.next()) {

                            if (!first) {
                                json.append(",");
                            }

                            json.append("{")
                                .append("\"id\":")
                                .append(qrs.getLong("id"))
                                .append(",\"question_number\":")
                                .append(nullableJson(
                                        qrs.getString("question_number")))
                                .append(",\"question_text\":")
                                .append(nullableJson(
                                        qrs.getString("question_text")))
                                .append(",\"suggested_marks\":")
                                .append(nullableJson(
                                        qrs.getString("suggested_marks")))
                                .append("}");

                            first = false;
                        }
                    }
                }

                json.append("]}");

                sendJson(exchange, 200, json.toString());
            }

        } catch (SQLException e) {

            System.err.println(
                    "Paper details query failed: " + e.getMessage());

            sendJson(exchange, 500,
                    "{\"error\":\"Unable to fetch paper details\"}");
        }
    }

    // =========================================================
    // SIMPLE JSON PARSER
    // =========================================================

    private static Object parseJson(String json) {
        return new JsonParser(json).parse();
    }

    private static final class JsonParser {

        private final String text;
        private int index = 0;

        JsonParser(String text) {
            this.text = text;
        }

        Object parse() {

            Object result = value();

            whitespace();

            if (index != text.length()) {
                throw new IllegalArgumentException("Invalid JSON.");
            }

            return result;
        }

        private void whitespace() {

            while (index < text.length() &&
                    Character.isWhitespace(text.charAt(index))) {
                index++;
            }
        }

        private Object value() {

            whitespace();

            if (index >= text.length()) {
                throw new IllegalArgumentException("Invalid JSON.");
            }

            char c = text.charAt(index);

            if (c == '{') return object();
            if (c == '[') return array();
            if (c == '"') return string();

            if (text.startsWith("true", index)) {
                index += 4;
                return Boolean.TRUE;
            }

            if (text.startsWith("false", index)) {
                index += 5;
                return Boolean.FALSE;
            }

            if (text.startsWith("null", index)) {
                index += 4;
                return null;
            }

            return number();
        }

        private Object number() {

            int start = index;

            if (index < text.length() &&
                    text.charAt(index) == '-') {
                index++;
            }

            if (index >= text.length()) {
                throw new IllegalArgumentException("Invalid JSON number.");
            }

            if (text.charAt(index) == '0') {
                index++;
            } else if (text.charAt(index) >= '1' &&
                    text.charAt(index) <= '9') {

                while (index < text.length() &&
                        Character.isDigit(text.charAt(index))) {
                    index++;
                }

            } else {
                throw new IllegalArgumentException("Invalid JSON number.");
            }

            if (index < text.length() &&
                    text.charAt(index) == '.') {

                index++;

                int fractionStart = index;

                while (index < text.length() &&
                        Character.isDigit(text.charAt(index))) {
                    index++;
                }

                if (fractionStart == index) {
                    throw new IllegalArgumentException("Invalid JSON number.");
                }
            }

            if (index < text.length() &&
                    (text.charAt(index) == 'e' ||
                     text.charAt(index) == 'E')) {

                index++;

                if (index < text.length() &&
                        (text.charAt(index) == '+' ||
                         text.charAt(index) == '-')) {
                    index++;
                }

                int exponentStart = index;

                while (index < text.length() &&
                        Character.isDigit(text.charAt(index))) {
                    index++;
                }

                if (exponentStart == index) {
                    throw new IllegalArgumentException("Invalid JSON number.");
                }
            }

            return text.substring(start, index);
        }

        private Map<String, Object> object() {

            Map<String, Object> map = new LinkedHashMap<>();

            index++;
            whitespace();

            if (take('}')) {
                return map;
            }

            while (true) {

                whitespace();

                if (index >= text.length() ||
                        text.charAt(index) != '"') {
                    throw new IllegalArgumentException(
                            "Invalid JSON object.");
                }

                String key = string();

                whitespace();
                require(':');

                map.put(key, value());

                whitespace();

                if (take('}')) {
                    return map;
                }

                require(',');
            }
        }

        private List<Object> array() {

            List<Object> list = new ArrayList<>();

            index++;
            whitespace();

            if (take(']')) {
                return list;
            }

            while (true) {

                list.add(value());

                whitespace();

                if (take(']')) {
                    return list;
                }

                require(',');
            }
        }

        private String string() {

            require('"');

            StringBuilder output = new StringBuilder();

            while (index < text.length()) {

                char c = text.charAt(index++);

                if (c == '"') {
                    return output.toString();
                }

                if (c == '\\') {

                    if (index >= text.length()) {
                        throw new IllegalArgumentException(
                                "Invalid JSON escape.");
                    }

                    char e = text.charAt(index++);

                    switch (e) {

                        case '"':
                            output.append('"');
                            break;

                        case '\\':
                            output.append('\\');
                            break;

                        case '/':
                            output.append('/');
                            break;

                        case 'b':
                            output.append('\b');
                            break;

                        case 'f':
                            output.append('\f');
                            break;

                        case 'n':
                            output.append('\n');
                            break;

                        case 'r':
                            output.append('\r');
                            break;

                        case 't':
                            output.append('\t');
                            break;

                        case 'u':

                            if (index + 4 > text.length()) {
                                throw new IllegalArgumentException(
                                        "Invalid Unicode escape.");
                            }

                            try {
                                output.append((char) Integer.parseInt(
                                        text.substring(index, index + 4), 16));
                            } catch (NumberFormatException ex) {
                                throw new IllegalArgumentException(
                                        "Invalid Unicode escape.");
                            }

                            index += 4;
                            break;

                        default:
                            throw new IllegalArgumentException(
                                    "Invalid JSON escape.");
                    }

                } else {

                    if (c < 0x20) {
                        throw new IllegalArgumentException(
                                "Invalid JSON control character.");
                    }

                    output.append(c);
                }
            }

            throw new IllegalArgumentException(
                    "Unterminated JSON string.");
        }

        private boolean take(char c) {

            if (index < text.length() &&
                    text.charAt(index) == c) {

                index++;
                return true;
            }

            return false;
        }

        private void require(char c) {

            whitespace();

            if (!take(c)) {
                throw new IllegalArgumentException(
                        "Invalid JSON syntax.");
            }
        }
    }

    // =========================================================
    // MAIN
    // =========================================================

    public static void main(String[] args) throws Exception {

        if (DB_PASSWORD == null || DB_PASSWORD.isBlank()) {
            System.err.println(
                    "ERROR: DB_PASSWORD is not set in this terminal.");
            return;
        }

        try (Connection connection = getConnection()) {
            System.out.println(
                    "MySQL connection successful: " +
                    connection.isValid(5));
        }

        HttpServer server = HttpServer.create(
                new InetSocketAddress("localhost", 8080), 0);

        server.createContext("/health", Main::handleHealth);
        server.createContext("/api/topics", Main::handleTopics);
        server.createContext("/api/analyze", Main::handleAnalyze);
        server.createContext("/api/papers", Main::handlePapers);
        server.createContext(
                "/api/papers/", Main::handlePaperDetails);
        server.createContext(
                "/api/questions/", Main::handleQuestionAnalysis);

        server.start();

        System.out.println("PaperMind AI backend is running!");
        System.out.println("Health:  http://localhost:8080/health");
        System.out.println("Topics:  http://localhost:8080/api/topics");
        System.out.println("Papers:  http://localhost:8080/api/papers");
        System.out.println("Analyze question: POST /api/analyze");
        System.out.println("Extract: POST /api/papers/{id}/extract");
        System.out.println("Analyze paper: POST /api/papers/{id}/analyze");
        System.out.println("Get analysis: GET /api/questions/{id}/analysis");
        System.out.println("Press Ctrl+C to stop.");
    }
}
