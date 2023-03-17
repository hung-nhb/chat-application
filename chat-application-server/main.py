import socket
import tkinter
from threading import Thread
import json


def push_notification(text):
    notification.config(state="normal")
    notification.insert(tkinter.END, text + ".\n")
    notification.config(state="disabled")


def handle_client(client, address):
    username, port_p2p = client.recv(buffer_size).decode("utf8").split("|")
    usernames.append(username)
    push_notification(username + " has connected")

    index_user = 0

    for user in database:
        if user["username"] == username:
            user["address"] = address[0] + "," + port_p2p
            json.dump(database, open("db.json", "w"))

            list_friends = user["listFriends"]
            list_friends_online = []
            list_address = []

            for friend in list_friends:
                for item in database:
                    if item["username"] == friend:
                        if item["address"] is not None:
                            list_friends_online.append(friend)
                            list_address.append(item["address"])
                            clients[usernames.index(friend)].send(
                                ("More online friend:" + username + "|" + address[0] + "," + port_p2p).encode("utf8"))
                        break

            client.send(("Online friends:" + "|".join(list_friends_online)).encode("utf8"))
            client.recv(buffer_size).decode("utf8")

            client.send(("Address friends:" + "|".join(list_address)).encode("utf8"))
            client.recv(buffer_size).decode("utf8")

            list_friends_offline = list(set(list_friends) ^ set(list_friends_online))
            client.send(("Offline friends:" + "|".join(list_friends_offline)).encode("utf8"))
            client.recv(buffer_size).decode("utf8")

            break

        index_user += 1

    else:
        database.append({"username": username, "address": address[0] + "," + port_p2p, "listFriends": []})

    while True:
        title, message, *_ = client.recv(buffer_size).decode("utf8").split(":") + [""]
        if title != "Command" or title != "Add friend" or title != "Delete friend":
            client.send("Done".encode("utf8"))

        if title == "Delete friend":
            database[index_user]["listFriends"].remove(message)
            for user in database:
                if user["username"] == message:
                    user["listFriends"].remove(username)
                    json.dump(database, open("db.json", "w"))

                    if user["address"] is not None:
                        clients[usernames.index(message)].send(("Delete friend:" + username).encode("utf8"))

                    break

        elif title == "Add friend":
            for user in database:
                if user["username"] == message:
                    database[index_user]["listFriends"].append(message)
                    user["listFriends"].append(username)

                    json.dump(database, open("db.json", "w"))

                    if user["address"] is None:
                        client.send(("Add friend:" + message + "|Offline").encode("utf8"))
                    else:
                        client.send(("Add friend:" + message + "|" + user["address"]).encode("utf8"))
                        clients[usernames.index(message)].send(
                            ("Add friend:" + username + "|" + address[0] + "," + port_p2p).encode("utf8"))

                    break

            else:
                client.send("Add friend:$NOT FOUND$".encode("utf8"))

        elif title == "Command":
            if message == "QUIT":
                index = usernames.index(username)
                del clients[index]
                del usernames[index]
                client.close()

                database[index_user]["address"] = None
                json.dump(database, open("db.json", "w"))

                push_notification(username + " has disconnected")


def client_connection():
    while True:
        client, address = server.accept()
        clients.append(client)
        Thread(target=handle_client, args=(client, address)).start()


def start_clicked():
    host = socket.gethostname()
    address = socket.gethostbyname(host)
    port = port_text.get()
    push_notification("Server start at IP: " + address + ", Port: " + port)
    server.bind((address, int(port)))
    server.listen(5)
    Thread(target=client_connection).start()


def stop_clicked():
    for user in database:
        user["address"] = None
    json.dump(database, open("db.json", "w"))

    try:
        for client in clients:
            client.send("System:Server is stopped".encode("utf8"))
            client.close()
        server.close()
    except OSError:
        pass

    push_notification("Server is stopped")


def online_users_clicked():
    push_notification("")
    for user in database:
        if user["address"] is not None:
            push_notification(user["username"] + " is online")


def clear_clicked():
    notification.config(state="normal")
    notification.delete("1.0", tkinter.END)
    notification.config(state="disabled")


def on_closing():
    stop_clicked()
    app.quit()


if __name__ == "__main__":
    buffer_size = 1024
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    database = json.load(open("db.json"))
    clients = []
    usernames = []

    app = tkinter.Tk()
    app.title("Chat Application Server")
    app.resizable(False, False)

    notification = tkinter.Text(app, width=50, height=15, state="disabled")
    notification.pack(padx=10, pady=10)

    control_frame = tkinter.Frame(app)
    control_frame.pack(padx=10)

    start_button = tkinter.Button(control_frame, text="Start", command=start_clicked)
    start_button.grid(row=0, column=0)

    stop_button = tkinter.Button(control_frame, text="Stop", command=stop_clicked)
    stop_button.grid(row=1, column=0, pady=10)

    port_label = tkinter.Label(control_frame, text="Port:")
    port_label.grid(row=0, column=1, padx=(10, 0))

    port_text = tkinter.Entry(control_frame)
    port_text.grid(row=0, column=2, padx=(0, 10))

    online_button = tkinter.Button(control_frame, text="Online Users", command=online_users_clicked)
    online_button.grid(row=0, column=3)

    clear_button = tkinter.Button(control_frame, text="Clear", command=clear_clicked)
    clear_button.grid(row=1, column=3, pady=10)

    app.protocol("WM_DELETE_WINDOW", on_closing)

    app.mainloop()
