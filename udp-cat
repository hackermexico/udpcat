// udp_cat_fd_file.go - UDP Cat Full-Duplex OIHEC Edition (con envío de archivos)
// Autor: Héctor López - OIHEC
// Descripción: Netcat UDP avanzado con chat full-duplex, escucha, envío, y transferencia de archivos con ACKs y reintentos.
// NOTA: UDP es no fiable. Este implementa un simple stop-and-wait por chunk con ACKs y reintentos.

package main

import (
	"bufio"
	"bytes"
	"flag"
	"fmt"
	"io"
	"net"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"sync"
	"time"
)

const (
	// Colores
	red    = "\033[31m"
	green  = "\033[32m"
	yellow = "\033[33m"
	cyan   = "\033[36m"
	reset  = "\033[0m"

	// Protocolo
	CTRL_PREFIX = "CTRL|"   // Mensajes de control: CTRL|START|filename|filesize  - CTRL|END|filename
	DATA_PREFIX = "DATA|"   // DATA|seq|<bytes...>
	ACK_PREFIX  = "ACK|"    // ACK|seq
	CHUNK_SIZE  = 1024     // bytes por paquete de datos
	TIMEOUT     = 2 * time.Second
	MAX_RETRIES = 5
)

// Banner
func banner() {
	fmt.Println(cyan + "================================================" + reset)
	fmt.Println(green + "    UDP Cat Full-Duplex - OIHEC Edition v3.0" + reset)
	fmt.Println(yellow + "    Netcat UDP en Go — chat, listen, send, file" + reset)
	fmt.Println(cyan + "================================================" + reset)
}

// Menú
func menu() {
	fmt.Println("\n" + green + "[1]" + reset + " Escuchar UDP")
	fmt.Println(green + "[2]" + reset + " Enviar UDP (mensaje)")
	fmt.Println(green + "[3]" + reset + " Chat Full-Duplex")
	fmt.Println(green + "[4]" + reset + " Enviar archivo")
	fmt.Println(green + "[5]" + reset + " Salir")
	fmt.Print(yellow + "Selecciona una opción: " + reset)
}

// --- UTIL: parse paquete UDP ---
func startsWith(b []byte, prefix string) bool {
	return len(b) >= len(prefix) && string(b[:len(prefix)]) == prefix
}

// --- LISTENER y RECEPCIÓN DE ARCHIVOS ---
type recvFile struct {
	f         *os.File
	expected  int    // siguiente seq esperado (0-based)
	totalSize int64
	received  int64
	lock      sync.Mutex
}

var recvFiles = struct {
	m map[string]*recvFile
	sync.Mutex
}{m: make(map[string]*recvFile)}

// handleIncoming procesa paquetes entrantes (mensajes, control, datos)
func handleIncoming(conn *net.UDPConn, b []byte, addr *net.UDPAddr) {
	now := time.Now().Format("15:04:05")
	if startsWith(b, CTRL_PREFIX) {
		// CTRL|START|filename|filesize
		parts := strings.SplitN(string(b), "|", 5)
		if len(parts) >= 4 && parts[1] == "START" {
			filename := filepath.Base(parts[2])
			filesize, _ := strconv.ParseInt(parts[3], 10, 64)
			recvFiles.Lock()
			if _, exists := recvFiles.m[filename]; exists {
				// ya existe: eliminar y reabrir
				recvFiles.m[filename].f.Close()
			}
			f, err := os.Create(filename)
			if err != nil {
				fmt.Println(red+"[ERROR] no puede crear archivo"+reset, err)
				recvFiles.Unlock()
				return
			}
			recvFiles.m[filename] = &recvFile{f: f, expected: 0, totalSize: filesize, received: 0}
			recvFiles.Unlock()
			fmt.Printf(cyan+"[%s] Inicio transferencia: %s (%d bytes) desde %s\n"+reset, now, filename, filesize, addr)
			return
		} else if len(parts) >= 3 && parts[1] == "END" {
			filename := filepath.Base(parts[2])
			recvFiles.Lock()
			if rf, ok := recvFiles.m[filename]; ok {
				rf.f.Close()
				fmt.Printf(green+"[%s] Archivo recibido: %s (%d bytes)\n"+reset, now, filename, rf.received)
				delete(recvFiles.m, filename)
			}
			recvFiles.Unlock()
			return
		}
	} else if startsWith(b, DATA_PREFIX) {
		// DATA|seq|<payload>
		// Encontrar la segunda '|' para separar seq y payload
		parts := bytes.SplitN(b, []byte("|"), 3)
		if len(parts) < 3 {
			return
		}
		seqStr := string(parts[1])
		payload := parts[2]
		seq, err := strconv.Atoi(seqStr)
		if err != nil {
			return
		}
		// Intentamos asociar el payload a algún archivo abierto (podemos hacer matching simple por último archivo activo)
		recvFiles.Lock()
		// Buscamos archivo con expected == seq
		var targetName string
		for name, rf := range recvFiles.m {
			if rf.expected == seq {
				targetName = name
				break
			}
		}
		if targetName == "" {
			// No encontramos archivo que espere este seq, ignoramos (pero respondemos ACK para que sender avance si lo desea)
			ack := []byte(ACK_PREFIX + strconv.Itoa(seq))
			conn.WriteToUDP(ack, addr)
			recvFiles.Unlock()
			return
		}
		rf := recvFiles.m[targetName]
		rf.lock.Lock()
		_, werr := rf.f.Write(payload)
		if werr == nil {
			rf.received += int64(len(payload))
			rf.expected++
		}
		rf.lock.Unlock()
		// enviar ACK
		ack := []byte(ACK_PREFIX + strconv.Itoa(seq))
		conn.WriteToUDP(ack, addr)
		recvFiles.Unlock()
		fmt.Printf(cyan+"[%s] %s: recibido chunk %d (%d bytes)\n"+reset, now, targetName, seq, len(payload))
		return
	} else {
		// Texto plano: mostrar
		fmt.Printf(cyan+"[%s] %s: "+reset+"%s\n", now, addr, string(b))
	}
}

// listenUDP con manejo concurrente de archivos y mensajes
func listenUDP(addr string) {
	udpAddr, err := net.ResolveUDPAddr("udp", addr)
	if err != nil {
		fmt.Println(red+"[Error resolviendo]"+reset, err)
		return
	}
	conn, err := net.ListenUDP("udp", udpAddr)
	if err != nil {
		fmt.Println(red+"[Error escuchando]"+reset, err)
		return
	}
	defer conn.Close()
	fmt.Println(green+"[*] Escuchando en", addr+reset)

	for {
		buf := make([]byte, CHUNK_SIZE+512) // suficiente para header + chunk
		n, remote, err := conn.ReadFromUDP(buf)
		if err != nil {
			fmt.Println(red+"[Error lectura]"+reset, err)
			continue
		}
		// procesar en goroutine para no bloquear
		data := make([]byte, n)
		copy(data, buf[:n])
		go handleIncoming(conn, data, remote)
	}
}

// --- ENVÍO DE MENSAJES (simple) ---
func sendUDP(addr, message string) {
	rAddr, err := net.ResolveUDPAddr("udp", addr)
	if err != nil {
		fmt.Println(red+"[Error resolviendo]"+reset, err)
		return
	}
	conn, err := net.DialUDP("udp", nil, rAddr)
	if err != nil {
		fmt.Println(red+"[Error conectando]"+reset, err)
		return
	}
	defer conn.Close()
	_, err = conn.Write([]byte(message))
	if err != nil {
		fmt.Println(red+"[Error enviando]"+reset, err)
		return
	}
	fmt.Println(green+"[OK] Mensaje enviado a", addr+reset)
}

// --- CHAT FULL-DUPLEX (recibe y permite enviar) ---
func chatUDP(localAddr, remoteAddr string) {
	lAddr, err := net.ResolveUDPAddr("udp", localAddr)
	if err != nil {
		fmt.Println(red+"[Error addr local]"+reset, err)
		return
	}
	rAddr, err := net.ResolveUDPAddr("udp", remoteAddr)
	if err != nil {
		fmt.Println(red+"[Error addr remota]"+reset, err)
		return
	}

	conn, err := net.ListenUDP("udp", lAddr)
	if err != nil {
		fmt.Println(red+"[Error escuchando]"+reset, err)
		return
	}
	defer conn.Close()

	fmt.Println(green+"[*] Chat Full-Duplex iniciado"+reset)
	fmt.Println(yellow+"Escribe mensajes. Usa /sendfile <ruta> para enviar archivos. Ctrl+C para salir."+reset)

	// Goroutine lectora
	go func() {
		for {
			buf := make([]byte, CHUNK_SIZE+512)
			n, addr, err := conn.ReadFromUDP(buf)
			if err != nil {
				fmt.Println(red+"[Error lectura]"+reset, err)
				continue
			}
			data := make([]byte, n)
			copy(data, buf[:n])
			handleIncoming(conn, data, addr)
		}
	}()

	// Escritor que envía al remote
	reader := bufio.NewReader(os.Stdin)
	for {
		text, _ := reader.ReadString('\n')
		text = strings.TrimSpace(text)
		if text == "" {
			continue
		}
		if strings.HasPrefix(text, "/sendfile ") {
			path := strings.TrimSpace(strings.TrimPrefix(text, "/sendfile "))
			if path != "" {
				go sendFileUDP("0.0.0.0:0", remoteAddr, path) // uso puerto efímero local
			}
			continue
		}
		_, err := conn.WriteToUDP([]byte(text), rAddr)
		if err != nil {
			fmt.Println(red+"[Error enviando]"+reset, err)
		}
	}
}

// --- ENVÍO DE ARCHIVO (stop-and-wait por chunk con ACKs) ---
func sendFileUDP(localAddr, remoteAddr, path string) {
	// Validar archivo
	finfo, err := os.Stat(path)
	if err != nil {
		fmt.Println(red+"[ERROR] archivo no encontrado:"+reset, err)
		return
	}
	if finfo.IsDir() {
		fmt.Println(red + "[ERROR] La ruta es un directorio" + reset)
		return
	}

	// Preparar conexión UDP local (puerto efímero o especificado)
	lAddr, _ := net.ResolveUDPAddr("udp", localAddr)
	rAddr, err := net.ResolveUDPAddr("udp", remoteAddr)
	if err != nil {
		fmt.Println(red+"[ERROR] dirección remota inválida"+reset, err)
		return
	}
	conn, err := net.ListenUDP("udp", lAddr)
	if err != nil {
		fmt.Println(red+"[ERROR] no se pudo abrir socket local"+reset, err)
		return
	}
	defer conn.Close()

	// Abrir archivo
	f, err := os.Open(path)
	if err != nil {
		fmt.Println(red+"[ERROR] abrir archivo"+reset, err)
		return
	}
	defer f.Close()

	filename := filepath.Base(path)
	filesize := finfo.Size()

	// Enviar mensaje START
	startMsg := []byte(CTRL_PREFIX + "START|" + filename + "|" + strconv.FormatInt(filesize, 10))
	_, err = conn.WriteToUDP(startMsg, rAddr)
	if err != nil {
		fmt.Println(red+"[ERROR] enviando START"+reset, err)
		return
	}
	fmt.Println(green+"[+] Iniciando envío:", filename, filesize, "bytes"+reset)

	// Modo stop-and-wait: enviar chunk, esperar ACK seq
	reader := bufio.NewReader(f)
	seq := 0
	buf := make([]byte, CHUNK_SIZE)
	for {
		n, err := io.ReadFull(reader, buf)
		if err == io.ErrUnexpectedEOF || err == io.EOF {
			// último fragmento con n bytes (si n==0, file terminado)
			if n == 0 {
				break
			}
			// procesar último fragmento
		} else if err != nil && err != io.ErrUnexpectedEOF {
			// err may be io.ErrUnexpectedEOF handled above, but other errors stop
			if err != nil {
				fmt.Println(red+"[ERROR] leyendo archivo"+reset, err)
				return
			}
		}

		dataPacket := append([]byte(DATA_PREFIX+strconv.Itoa(seq)+"|"), buf[:n]...)
		// reintentos
		sent := false
		for attempt := 0; attempt < MAX_RETRIES; attempt++ {
			_, err = conn.WriteToUDP(dataPacket, rAddr)
			if err != nil {
				fmt.Println(red+"[ERROR] enviando chunk"+reset, err)
			}
			// Esperar ACK
			conn.SetReadDeadline(time.Now().Add(TIMEOUT))
			ackBuf := make([]byte, 128)
			nr, _, rerr := conn.ReadFromUDP(ackBuf)
			if rerr != nil {
				// timeout o read error -> retry
				fmt.Println(yellow+"[!] timeout esperando ACK, reintentando..."+reset)
				continue
			}
			ack := string(ackBuf[:nr])
			if strings.HasPrefix(ack, ACK_PREFIX) {
				ackSeqStr := strings.TrimPrefix(ack, ACK_PREFIX)
				ackSeq, _ := strconv.Atoi(ackSeqStr)
				if ackSeq == seq {
					sent = true
					break
				}
			}
		}
		if !sent {
			fmt.Println(red+"[ERROR] No se recibió ACK para chunk", seq, "-> abortando"+reset)
			return
		}
		fmt.Printf(green+"[+] chunk %d enviado y ACK recibido (%d bytes)\n"+reset, seq, n)
		seq++
		// Si n < CHUNK_SIZE fue último
		if n < CHUNK_SIZE {
			break
		}
	}

	// Enviar END
	endMsg := []byte(CTRL_PREFIX + "END|" + filename)
	_, err = conn.WriteToUDP(endMsg, rAddr)
	if err != nil {
		fmt.Println(red+"[ERROR] enviando END"+reset, err)
		return
	}
	fmt.Println(green+"[OK] Envío completado:", filename+reset)
}

// --- MAIN + FLAGS + MENÚ ---
func main() {
	mode := flag.String("mode", "", "Modo: listen, send, chat, file-send")
	host := flag.String("host", "127.0.0.1", "Host destino")
	port := flag.String("port", "9999", "Puerto destino")
	msg := flag.String("msg", "", "Mensaje para enviar (modo send)")
	lport := flag.String("lport", "9998", "Puerto local para chat/listen")
	filepathFlag := flag.String("file", "", "Ruta de archivo (modo file-send o send -file)")
	flag.Parse()

	banner()

	if *mode != "" {
		switch *mode {
		case "listen":
			listenUDP("0.0.0.0:" + *port)
		case "send":
			if strings.TrimSpace(*msg) == "" && strings.TrimSpace(*filepathFlag) == "" {
				fmt.Println(red + "[!] Debes indicar -msg o -file para modo send" + reset)
				return
			}
			if *filepathFlag != "" {
				sendFileUDP("0.0.0.0:0", *host+":"+*port, *filepathFlag)
			} else {
				sendUDP(*host+":"+*port, *msg)
			}
		case "chat":
			chatUDP("0.0.0.0:"+*lport, *host+":"+*port)
		case "file-send":
			if strings.TrimSpace(*filepathFlag) == "" {
				fmt.Println(red + "[!] Debes indicar -file con la ruta" + reset)
				return
			}
			sendFileUDP("0.0.0.0:0", *host+":"+*port, *filepathFlag)
		default:
			fmt.Println(red + "[!] Modo no válido" + reset)
		}
		return
	}

	// Menú interactivo
	reader := bufio.NewReader(os.Stdin)
	for {
		menu()
		choice, _ := reader.ReadString('\n')
		choice = strings.TrimSpace(choice)
		switch choice {
		case "1":
			fmt.Print("Puerto de escucha: ")
			p, _ := reader.ReadString('\n')
			p = strings.TrimSpace(p)
			listenUDP("0.0.0.0:" + p)
		case "2":
			fmt.Print("Host: ")
			h, _ := reader.ReadString('\n')
			h = strings.TrimSpace(h)
			fmt.Print("Puerto: ")
			p, _ := reader.ReadString('\n')
			p = strings.TrimSpace(p)
			fmt.Print("Mensaje: ")
			m, _ := reader.ReadString('\n')
			m = strings.TrimSpace(m)
			sendUDP(h+":"+p, m)
		case "3":
			fmt.Print("Puerto local: ")
			lp, _ := reader.ReadString('\n')
			lp = strings.TrimSpace(lp)
			fmt.Print("Host remoto: ")
			h, _ := reader.ReadString('\n')
			h = strings.TrimSpace(h)
			fmt.Print("Puerto remoto: ")
			p, _ := reader.ReadString('\n')
			p = strings.TrimSpace(p)
			fmt.Println(yellow + "Nota: en chat puedes usar /sendfile <ruta>" + reset)
			chatUDP("0.0.0.0:"+lp, h+":"+p)
		case "4":
			fmt.Print("Host remoto: ")
			h, _ := reader.ReadString('\n')
			h = strings.TrimSpace(h)
			fmt.Print("Puerto remoto: ")
			p, _ := reader.ReadString('\n')
			p = strings.TrimSpace(p)
			fmt.Print("Ruta archivo: ")
			fp, _ := reader.ReadString('\n')
			fp = strings.TrimSpace(fp)
			sendFileUDP("0.0.0.0:0", h+":"+p, fp)
		case "5":
			fmt.Println(green + "[*] Saliendo..." + reset)
			os.Exit(0)
		default:
			fmt.Println(red + "[!] Opción no válida" + reset)
		}
	}
}
