package main

import (
	"bufio"
	"fmt"
	"log"
	"net"
)

func main() {
	conn, err := net.Dial("tcp", "127.0.0.1:8080")
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()

	fmt.Println("TCP client connected")

	var a, b, h float64

	fmt.Print("Enter first base a: ")
	fmt.Scan(&a)

	fmt.Print("Enter second base b: ")
	fmt.Scan(&b)

	fmt.Print("Enter height h: ")
	fmt.Scan(&h)

	msg := fmt.Sprintf("%f %f %f\n", a, b, h)

	msgByte := []byte(msg)

	_, err = conn.Write(msgByte)
	if err != nil {
		log.Fatal(err)
	}

	reader := bufio.NewReader(conn)

	response, err := reader.ReadString('\n')
	if err != nil {
		log.Fatal(err)
	}

	fmt.Print("Server response: ", response)
}
