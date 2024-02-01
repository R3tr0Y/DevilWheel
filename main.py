import asyncio

class Server:
    def __init__(self):
        self.clients = {}
        self.games = {}
    
    async def handle_client(self, reader, writer):
        try:
            writer.write("Input your username:".encode())
            await writer.drain()

            data = await reader.read(100)
            username = data.decode().strip()

            if not self.is_username_available(username):
                writer.write("This username is not available. Quitting!\n".encode())
                await writer.drain()
                return

            self.clients[username] = writer
            await self.start_session(username, reader, writer)

        except asyncio.CancelledError:
            pass
        finally:
            writer.close()

    def is_username_available(self, username):
        return username not in self.clients
    
    async def start_session(self, username, reader, writer):
        writer.write(f"Hello, {username}! Try type /help.\n".encode())
        try:
            while True:
                writer.write(f"".encode())
                await writer.drain()

                data = await reader.read(100)
                message = data.decode().strip()

                response = ""

                if message == "/quit" or message == "/exit":
                    writer.write("\nBye.\n".encode())
                    break
                elif message == "/help":
                    response = "\nAvailable commands:\n/help - Show this help\n/quit - Quit the session\n/message user - Send a private message to user\n/list - List online users\n/pair  - Pair a user to a game of Russian Roulette\n"
                elif message.startswith("/message"):
                    recipient, msg = message.split(" ", 2)[1:]
                    await self.send_private_message(username, recipient, msg)
                elif message == "/list":
                    online_users = [u for u in self.clients]
                    response = f"\nOnline users: {', '.join(online_users)}\n"
                elif message == "/pair":
                    response = "\nNot yet...\n"
                elif message.startswith('/'):
                    response = "\nCommand false.\n"
                else:
                    # response = f"You said: {message}\n"
                    if message.strip() != "":
                        await self.broadcast_message(username, message)

                writer.write(response.encode())
                await writer.drain()

        except asyncio.CancelledError:
            pass
        finally:
            del self.clients[username]
            if username in self.games:
                del self.games[username]

            writer.close()
    async def broadcast_message(self, sender, message):
        for user, user_writer in self.clients.items():
            if user != sender:
                user_writer.write(f"{sender}: {message}\n".encode())
                await user_writer.drain()
    async def send_private_message(self, sender, recipient, message):
        recipient_writer = self.clients[recipient]

        if recipient_writer:
            recipient_writer.write(f"Private message from {sender}: {message}\n".encode())
            await recipient_writer.drain()

    async def main(self):
        server = await asyncio.start_server(
            self.handle_client, '127.0.0.1', 8080)

        addr = server.sockets[0].getsockname()
        print(f'Serving on {addr}')

        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    chat_server = Server()
    asyncio.run(chat_server.main())