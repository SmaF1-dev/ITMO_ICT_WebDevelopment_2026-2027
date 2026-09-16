package main

import (
	"fmt"
	"log"
	"net"
	"os"
)

func handleConnection(conn net.Conn) {
	defer conn.Close()
	buffer := make([]byte, 4096)

	n, err := conn.Read(buffer)
	if err != nil {
		log.Fatal(err)
		return
	}

	request := string(buffer[:n])

	fmt.Println("Request:")
	fmt.Println(request)

	html, err := os.ReadFile("index.html")
	if err != nil {
		log.Fatal(err)
		return
	}

	response := fmt.Sprintf(
		"HTTP/1.1 200 OK\r\n"+
			"Content-Type: text/html; charset=utf-8\r\n"+
			"Content-Length: %d\r\n"+
			"\r\n"+
			"%s",
		len(html),
		html,
	)

	_, err = conn.Write([]byte(response))
	if err != nil {
		log.Fatal(err)
		return
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
		handleConnection(conn)
	}

}
