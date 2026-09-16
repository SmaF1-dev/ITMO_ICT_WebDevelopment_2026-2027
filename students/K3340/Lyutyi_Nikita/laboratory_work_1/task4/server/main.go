package main

import (
	"bufio"
	"fmt"
	"log"
	"net"
	"strings"
	"sync"
)

type Client struct {
	name string
	conn net.Conn
}

var clients = make(map[net.Conn]*Client)
var mutex sync.Mutex

func broadcast(msg string, sender net.Conn) {
	mutex.Lock()
	defer mutex.Unlock()

	for _, client := range clients {
		if client.conn == sender {
			continue
		}

		_, err := client.conn.Write([]byte(msg))
		if err != nil {
			log.Println("Error sending message to ", client.name, " : ", err)
		}
	}
}

func handleConn(conn net.Conn) {
	defer conn.Close()

	reader := bufio.NewReader(conn)

	_, err := conn.Write([]byte("Enter your name: \n"))
	if err != nil {
		log.Println(err)
		return
	}

	name, err := reader.ReadString('\n')
	if err != nil {
		log.Println(err)
		return
	}

	name = strings.TrimSpace(name)

	client := &Client{
		name: name,
		conn: conn,
	}

	mutex.Lock()
	clients[conn] = client
	mutex.Unlock()

	fmt.Println(name, "connected")

	broadcast(
		fmt.Sprintf("%s joined the chat\n", name),
		conn,
	)

	for {
		msg, err := reader.ReadString('\n')
		if err != nil {
			break
		}

		msg = strings.TrimSpace(msg)

		if msg == "" {
			continue
		}

		if msg == "/exit" {
			break
		}

		fmt.Printf("%s: %s\n", name, msg)

		broadcast(
			fmt.Sprintf("%s: %s\n", name, msg),
			conn,
		)
	}

	mutex.Lock()
	delete(clients, conn)
	mutex.Unlock()

	fmt.Println(name, "disconnected")

	broadcast(
		fmt.Sprintf("%s left the chat\n", name),
		conn,
	)
}

func main() {
	listener, err := net.Listen("tcp", ":8080")
	if err != nil {
		log.Fatal(err)
	}
	defer listener.Close()

	fmt.Println("Chat server started on :8080")

	for {
		conn, err := listener.Accept()
		if err != nil {
			log.Println(err)
			continue
		}

		go handleConn(conn)
	}
}
