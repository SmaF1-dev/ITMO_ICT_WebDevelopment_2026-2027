package main

import (
	"bufio"
	"fmt"
	"log"
	"net"
)

func main() {
	listener, err := net.Listen("tcp", ":8080")
	if err != nil {
		log.Fatal(err)
	}

	defer listener.Close()

	fmt.Println("TCP server started on :8080")

	conn, err := listener.Accept()
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()

	fmt.Println("Client connected:", conn.RemoteAddr())

	reader := bufio.NewReader(conn)

	msg, err := reader.ReadString('\n')
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println("Received:", msg)

	var a, b, h float64

	_, err = fmt.Sscanf(msg, "%f %f %f", &a, &b, &h)
	if err != nil {
		log.Fatal(err)
	}

	area := (a + b) / 2 * h

	response := fmt.Sprintf("Trapezoid area: %.2f\n", area)

	responseByte := []byte(response)
	_, err = conn.Write(responseByte)
	if err != nil {
		log.Fatal(err)
	}
}
