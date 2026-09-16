package main

import (
	"bufio"
	"fmt"
	"log"
	"net"
	"os"
	"strings"
)

func receiveMessages(conn net.Conn) {
	reader := bufio.NewReader(conn)

	for {
		msg, err := reader.ReadString('\n')
		if err != nil {
			log.Println("\nDisconnected from server")
			os.Exit(0)
		}

		fmt.Printf("\r%s> ", msg)
	}
}

func main() {
	conn, err := net.Dial("tcp", "127.0.0.1:8080")
	if err != nil {
		log.Fatal(err)
	}
	defer conn.Close()

	fmt.Println("Connected to chat")

	go receiveMessages(conn)

	reader := bufio.NewReader(os.Stdin)

	for {
		fmt.Print("> ")

		msg, err := reader.ReadString('\n')
		if err != nil {
			log.Fatal(err)
		}

		_, err = conn.Write([]byte(msg))
		if err != nil {
			log.Fatal(err)
		}

		if strings.TrimSpace(msg) == "/exit" {
			return
		}
	}
}
