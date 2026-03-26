import { io } from 'socket.io-client';

const NAMESPACE = "/api/datasets-download-progress";

export const socket = io("http://127.0.0.1:5000",
{
    autoConnect: false,
    transports: ["websocket"],
    withCredentials: true
} )