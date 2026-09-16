package main

import (
	"bufio"
	"bytes"
	"fmt"
	"html/template"
	"io"
	"log"
	"net"
	"net/url"
	"strconv"
	"strings"
	"sync"
)

type Request struct {
	Method  string
	Path    string
	Headers map[string]string
	Body    string
}

type PageData struct {
	Grades map[string][]int
}

var grades = make(map[string][]int)
var mutex sync.Mutex

func parseRequest(reader *bufio.Reader) (*Request, error) {
	requestLine, err := reader.ReadString('\n')
	if err != nil {
		return nil, err
	}

	requestLine = strings.TrimSpace(requestLine)

	parts := strings.Split(requestLine, " ")
	if len(parts) != 3 {
		return nil, fmt.Errorf("invalid request line")
	}

	request := &Request{
		Method:  parts[0],
		Path:    parts[1],
		Headers: make(map[string]string),
	}

	for {
		line, err := reader.ReadString('\n')
		if err != nil {
			return nil, err
		}

		if line == "\r\n" {
			break
		}

		line = strings.TrimSpace(line)

		headerParts := strings.SplitN(line, ":", 2)
		if len(headerParts) != 2 {
			continue
		}

		key := strings.TrimSpace(headerParts[0])
		value := strings.TrimSpace(headerParts[1])

		request.Headers[key] = value
	}

	contentLength := 0

	if val, ok := request.Headers["Content-Length"]; ok {
		contentLength, err = strconv.Atoi(val)
		if err != nil {
			return nil, fmt.Errorf("invalid Content-Length")
		}
	}

	if contentLength > 0 {
		body := make([]byte, contentLength)

		_, err := io.ReadFull(reader, body)
		if err != nil {
			return nil, err
		}

		request.Body = string(body)
	}

	return request, nil
}

func sendResponse(
	conn net.Conn,
	status string,
	contentType string,
	body string,
	extraHeaders map[string]string,
) {
	response := fmt.Sprintf(
		"HTTP/1.1 %s\r\n"+
			"Content-Type: %s\r\n"+
			"Content-Length: %d\r\n",
		status,
		contentType,
		len([]byte(body)),
	)

	for key, val := range extraHeaders {
		response += fmt.Sprintf("%s: %s\r\n", key, val)
	}

	response += "\r\n"
	response += body

	_, err := conn.Write([]byte(response))
	if err != nil {
		log.Println("Error sending response:", err)
	}
}

func renderPage() (string, error) {
	tmpl, err := template.ParseFiles("index.html")
	if err != nil {
		return "", err
	}

	mutex.Lock()

	data := PageData{
		Grades: grades,
	}

	var body bytes.Buffer

	err = tmpl.Execute(&body, data)

	mutex.Unlock()

	if err != nil {
		return "", err
	}

	return body.String(), nil
}

func handleGet(conn net.Conn, requst *Request) {
	if requst.Path != "/" {
		sendResponse(
			conn,
			"404 Not Found",
			"text/plain; charset=utf-8",
			"404 Not Found",
			nil,
		)
		return
	}

	page, err := renderPage()
	if err != nil {
		log.Println("Template error:", err)

		sendResponse(
			conn,
			"500 Internal Server Error",
			"text/plain; charset=utf-8",
			"Internal Server Error",
			nil,
		)

		return
	}

	sendResponse(
		conn,
		"200 OK",
		"text/html; charset=utf-8",
		page,
		nil,
	)
}

func handlePost(conn net.Conn, request *Request) {
	if request.Path != "/grades" {
		sendResponse(
			conn,
			"404 Not Found",
			"text/plain; charset=utf-8",
			"404 Not Found",
			nil,
		)
		return
	}

	values, err := url.ParseQuery(request.Body)
	if err != nil {
		sendResponse(
			conn,
			"400 Bad Request",
			"text/plain; charset=utf-8",
			"Invalid form data",
			nil,
		)
		return
	}

	subject := strings.TrimSpace(values.Get("subject"))
	gradeString := values.Get("grade")

	if subject == "" {
		sendResponse(
			conn,
			"400 Bad Request",
			"text/plain; charset=utf-8",
			"Subject is required",
			nil,
		)
		return
	}

	grade, err := strconv.Atoi(gradeString)
	if err != nil || grade < 2 || grade > 5 {
		sendResponse(
			conn,
			"400 Bad Request",
			"text/plain; charset=utf-8",
			"Grade must be an integer from 2 to 5",
			nil,
		)
		return
	}

	mutex.Lock()
	grades[subject] = append(grades[subject], grade)
	mutex.Unlock()

	sendResponse(
		conn,
		"303 See Other",
		"text/plain; charset=utf-8",
		"",
		map[string]string{
			"Location": "/",
		},
	)
}

func handleConnection(conn net.Conn) {
	defer conn.Close()

	reader := bufio.NewReader(conn)

	request, err := parseRequest(reader)
	if err != nil {
		log.Println("Error parsing request:", err)
		return
	}

	fmt.Println("Method:", request.Method)
	fmt.Println("Path:", request.Path)

	if request.Body != "" {
		fmt.Println("Body:", request.Body)
	}

	switch request.Method {
	case "GET":
		handleGet(conn, request)
	case "POST":
		handlePost(conn, request)

	default:
		sendResponse(
			conn,
			"405 Method Not Allowed",
			"text/plain; charset=utf-8",
			"Method Not Allowed",
			nil,
		)
	}
}

func main() {
	listener, err := net.Listen("tcp", ":8080")
	if err != nil {
		log.Fatal(err)
	}
	defer listener.Close()

	fmt.Println("HTTP server started on http://localhost:8080")

	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Println(err)
			continue
		}

		go handleConnection(conn)
	}
}
