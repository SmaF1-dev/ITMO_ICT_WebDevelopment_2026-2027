package main

import (
	"fmt"
	"log"
	"net"
)

func main() {
	serverAddr, err := net.ResolveUDPAddr("udp", "127.0.0.1:8080")
	if err != nil {
		log.Fatal(err)
	}

	conn, err := net.DialUDP("udp", nil, serverAddr)
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()

	fmt.Println("UDP client started")

	msg := []byte("Hello, server")

	_, err = conn.Write(msg)
	if err != nil {
		log.Fatal(err)
	}

	buffer := make([]byte, 1024)

	n, err := conn.Read(buffer)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println("Received:", string(buffer[:n]))
}
