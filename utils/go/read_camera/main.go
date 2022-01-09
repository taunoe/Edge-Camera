package main

import (
        "log"
        "github.com/tarm/serial" // go get github.com/tarm/serial
)

func main() {
        c := &serial.Config{Name: "/dev/ttyACM0", Baud: 115200}
        ser, err := serial.OpenPort(c)
        if err != nil {
                log.Fatal(err)
        }
        
        /* Write
        n, err := ser.Write([]byte("test"))
        if err != nil {
                log.Fatal(err)
        }
        */
        
        // it reads random part. not line (\n)
        buf := make([]byte, 128)
        n, err := ser.Read(buf)
        if err != nil {
                log.Fatal(err)
        }
        log.Printf("%q", buf[:n])
}