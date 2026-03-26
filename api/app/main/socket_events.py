from flask_socketio import emit, join_room, disconnect
from flask import request
from app import socketio, SOCKET_NAMESPACE
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

@socketio.on('connect', namespace=SOCKET_NAMESPACE)
def handle_connect():
    try:
        verify_jwt_in_request()
        username = get_jwt_identity()

        room = f"user_{username}"
        join_room(room)

        print(f"User {username} connected")

    except Exception as e:
        print("JWT verification failed:", str(e))
        disconnect()

@socketio.on('disconnect', namespace=SOCKET_NAMESPACE)
def test_disconnect(reason):
    print('Client disconnected, reason:', reason)
    