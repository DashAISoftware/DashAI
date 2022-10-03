#!/usr/bin/bash
execute_gui() {
    cd "front/build"
    python -m http.server 3000
}

execute_api() {
    cd "back"
    uvicorn main:app --reload
}

execute_gui & execute_api