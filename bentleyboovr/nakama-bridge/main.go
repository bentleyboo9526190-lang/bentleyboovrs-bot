package main

import (
	"context"
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/ascii8/nakama-go"
)

type status struct {
	Service     string `json:"service"`
	Connection  string `json:"connection"`
	Server      string `json:"server"`
	CheckedAt   string `json:"checked_at"`
	Message     string `json:"message"`
}

func main() {
	addr := os.Getenv("NAKAMA_BRIDGE_ADDR")
	if addr == "" {
		addr = "127.0.0.1:8081"
	}

	client := nakama.New()
	mux := http.NewServeMux()

	mux.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		writeJSON(w, http.StatusOK, map[string]any{"ok": true, "service": "BentleyBooVR Nakama bridge"})
	})

	mux.HandleFunc("/status", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodGet {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}

		ctx, cancel := context.WithTimeout(r.Context(), 3*time.Second)
		defer cancel()

		result := status{
			Service:    "BentleyBooVR Nakama bridge",
			Connection: "unavailable",
			Server:     "http://127.0.0.1:7350",
			CheckedAt:  time.Now().UTC().Format(time.RFC3339),
			Message:    "Nakama did not respond to its health check.",
		}
		if err := client.Healthcheck(ctx); err == nil {
			result.Connection = "connected"
			result.Message = "Connected to the project-owned Nakama server."
			writeJSON(w, http.StatusOK, result)
			return
		}
		writeJSON(w, http.StatusServiceUnavailable, result)
	})

	server := &http.Server{
		Addr:              addr,
		Handler:           mux,
		ReadHeaderTimeout: 5 * time.Second,
	}
	log.Printf("BentleyBooVR Nakama bridge listening on http://%s", addr)
	log.Fatal(server.ListenAndServe())
}

func writeJSON(w http.ResponseWriter, code int, value any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(value)
}
