#!/usr/bin/bash
execute_gui() {
    cd "front/build"
    python -m http.server 3000
}

execute_api() {
    python3 back/main.py
}

execute_gui & execute_api