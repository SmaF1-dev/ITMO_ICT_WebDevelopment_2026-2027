package main

import (
	"fmt"
	"log"
	"net"
)

func main() {
	addr, err := net.ResolveUDPAddr("udp", ":8080")
	if err != nil {
		log.Fatal(err)
	}

	conn, err := net.ListenUDP("udp", addr)
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()

	fmt.Println("UDP server started on :8080")

	buffer := make([]byte, 1024)

	n, clientAddr, err := conn.ReadFromUDP(buffer)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println("Received:", string(buffer[:n]))

	msg := []byte("Hello, client")

	_, err = conn.WriteToUDP(msg, clientAddr)
	if err != nil {
		log.Fatal(err)
	}
}
