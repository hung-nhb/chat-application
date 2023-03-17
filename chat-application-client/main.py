import socket
from threading import Thread
import tkinter
from tkinter import filedialog


def push_offline_friend(text):
    friend_offline_list.config(state="normal")
    friend_offline_list.insert(tkinter.END, text + "\n")
    friend_offline_list.config(state="disabled")


def push_message(text):
    message_list.config(state="normal")
    message_list.insert(tkinter.END, text + "\n")
    message_list.config(state="disabled")


def clear_message():
    message_list.config(state="normal")
    message_list.delete('1.0', tkinter.END)
    message_list.config(state="disabled")


def handle_listen_p2p(conn):
    global list_friends_online

    while True:
        title, message, *_ = conn.recv(buffer_size).decode("utf8").split(":") + [None]
        conn.send("Done".encode("utf8"))

        if title == "Send file":
            username, filename = message.split("|")

            f = open(username + "_" + filename, "w")
            while True:
                data = conn.recv(buffer_size).decode("utf8")
                conn.send("Done".encode("utf8"))

                if data == "$EOF$":
                    conn.send("Done".encode("utf8"))
                    break

                f.write(data)
            f.close()

            notification = "System: You received a file \"" + filename + "\". It is saved as \"" \
                           + username + "_" + filename + "\" in the folder you run client."
            message_logs[list_friends_online.index(username)].append(notification)
            if list_friends_online.index(username) == friend_online_list.curselection()[0]:
                push_message(notification)

        elif title == "QUIT":
            index = list_friends_online.index(message)
            list_friends_online.remove(message)
            friend_online_list.delete(index)

            removed_client = clients.pop(index)
            removed_client.close()
            conn.close()
            del clients_p2p[index]

            push_message(message + " has disconnected")

        else:
            message_logs[list_friends_online.index(title)].append(title + ": " + message)
            if list_friends_online.index(title) == friend_online_list.curselection()[0]:
                push_message(title + ": " + message)


def listen_p2p(server):
    while True:
        conn, address = server.accept()
        clients_p2p.append(conn)
        Thread(target=handle_listen_p2p, args=(conn,)).start()


def create_server_p2p():
    host_server = socket.gethostname()
    address_server = socket.gethostbyname(host_server)
    port_server = port_p2p_text.get()
    server_p2p.bind((address_server, int(port_server)))
    push_message("Create P2P at Hostname: " + address_server + ", Port: " + port_server)
    server_p2p.listen(5)
    Thread(target=listen_p2p, args=(server_p2p,)).start()


def handle_client():
    global list_friends_online
    global list_friends_offline
    global clients
    global client

    while True:
        title, message, *_ = client.recv(buffer_size).decode("utf8").split(":") + [""]
        if title != "System" or title != "Add friend" or title != "Delete friend":
            client.send("Done".encode("utf8"))

        if title == "Online friends" and len(message) > 0:
            list_friends_online = message.split("|")
            for user in list_friends_online:
                friend_online_list.insert(tkinter.END, user)
                message_logs.append([])

        elif title == "Address friends" and len(message) > 0:
            list_address = message.split("|")
            for address in list_address:
                host_temp, port_temp = address.split(",")
                client_p2p = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client_p2p.connect((host_temp, int(port_temp)))
                clients.append(client_p2p)

        elif title == "Offline friends" and len(message) > 0:
            list_friends_offline = message.split("|")
            for user in list_friends_offline:
                push_offline_friend(user)

        elif title == "More online friend":
            friend_username, friend_address = message.split("|")
            host_temp, port_temp = friend_address.split(",")

            client_p2p = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_p2p.connect((host_temp, int(port_temp)))
            clients.append(client_p2p)

            list_friends_online.append(friend_username)
            friend_online_list.insert(tkinter.END, friend_username)
            message_logs.append([])

            list_friends_offline.remove(friend_username)
            friend_offline_list.config(state="normal")
            friend_offline_list.delete("1.0", tkinter.END)
            friend_offline_list.config(state="disabled")

            for user in list_friends_offline:
                push_offline_friend(user)

        elif title == "Delete friend":
            if message in list_friends_offline:
                list_friends_offline.remove(message)
                friend_offline_list.config(state="normal")
                friend_offline_list.delete("1.0", tkinter.END)
                friend_offline_list.config(state="disabled")

                for user in list_friends_offline:
                    push_offline_friend(user)

            elif message in list_friends_online:
                index = list_friends_online.index(message)
                list_friends_online.remove(message)
                friend_online_list.delete(index)

                message_logs.pop(index)

                removed_client = clients.pop(index)
                removed_client.close()
                removed_client_p2p = clients_p2p.pop(index)
                removed_client_p2p.close()

        elif title == "Add friend":
            if message == "$NOT FOUND$":
                push_message("System: Can't find the user have name \"" + modify_friend_content.get() + "\"")

            else:
                modify_friend_content.set("")
                friend, address = message.split("|")

                if address == "Offline":
                    list_friends_offline.append(friend)
                    push_offline_friend(friend)
                else:
                    host_temp, port_temp = address.split(",")
                    client_p2p = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    client_p2p.connect((host_temp, int(port_temp)))
                    clients.append(client_p2p)

                    list_friends_online.append(friend)
                    friend_online_list.insert(tkinter.END, friend)
                    message_logs.append([])

        elif title == "System":
            push_message("System: " + message)


def connect_clicked():
    global client

    create_server_p2p()

    host = host_text.get()
    port = port_text.get()
    username = username_text.get()

    if host == "" or port == "" or username == "":
        push_message("Please fill out the form completely")

    if username == "Send file" or username == "QUIT":
        push_message("Please enter another username")

    try:
        client.connect((host, int(port)))
    except ConnectionRefusedError:
        push_message("Can't connect, please check again")
        return

    push_message("Connected to server at Hostname: " + host + ", Port: " + port)
    client.send((username + "|" + port_p2p_text.get()).encode("utf8"))

    Thread(target=handle_client).start()


def send_file_clicked():
    index = friend_online_list.curselection()[0]
    filename = filedialog.askopenfilename(initialdir="/", title="Select a File")
    clients[index].send(("Send file:" + username_text.get() + "|" + filename[filename.rfind("/") + 1:]).encode("utf8"))
    clients[index].recv(buffer_size).decode("utf8")

    f = open(filename)
    data = f.read(buffer_size)
    while data:
        clients[index].send(data.encode("utf8"))
        clients[index].recv(buffer_size).decode("utf8")
        data = f.read(buffer_size)

    clients[index].send("$EOF$".encode("utf8"))
    clients[index].recv(buffer_size).decode("utf8")

    f.close()

    push_message("System: You sent a file \"" + filename[filename.rfind("/") + 1:] + "\"")
    index = friend_online_list.curselection()[0]
    message_logs[index].append(message_content.get())


def send_clicked():
    if len(friend_online_list.curselection()) == 0:
        push_message("Please choose a friend to chat")
    else:
        message = message_content.get()
        message_content.set("")
        push_message("You: " + message)
        index = friend_online_list.curselection()[0]
        message_logs[index].append("You: " + message)
        clients[index].send((username_text.get() + ":" + message).encode("utf8"))


def on_select_online_friend(event):
    clear_message()
    if len(event.widget.curselection()) > 0:
        for message in message_logs[event.widget.curselection()[0]]:
            push_message(message)


def add_friend_clicked():
    global client
    friend = modify_friend_content.get()
    if friend != "" and friend != username_text.get() \
            and friend not in list_friends_online and friend not in list_friends_offline:
        client.send(("Add friend:" + friend).encode("utf8"))


def delete_friend_clicked():
    global client
    friend = modify_friend_content.get()
    if friend != "":
        if friend in list_friends_offline:
            list_friends_offline.remove(friend)
            friend_offline_list.config(state="normal")
            friend_offline_list.delete("1.0", tkinter.END)
            friend_offline_list.config(state="disabled")

            for user in list_friends_offline:
                push_offline_friend(user)

            client.send(("Delete friend:" + friend).encode("utf8"))
            modify_friend_content.set("")

        elif friend in list_friends_online:
            index = list_friends_online.index(friend)
            list_friends_online.remove(friend)
            friend_online_list.delete(index)
            removed_client = clients.pop(index)
            removed_client.close()
            message_logs.pop(index)

            client.send(("Delete friend:" + friend).encode("utf8"))
            modify_friend_content.set("")

        else:
            push_message("Don't have user with name \"" + modify_friend_content.get() + "\" in your list friends")


def disconnect_clicked():
    global client
    try:
        for p2p in clients:
            p2p.send(("QUIT:" + username_text.get()).encode("utf8"))
            p2p.close()

        for p2p in clients_p2p:
            p2p.close()
        server_p2p.close()

        client.send("Command:QUIT".encode("utf8"))
        client.close()
    except OSError:
        push_message("No connection detected")
    finally:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        push_message("Disconnected to server")


def on_closing():
    disconnect_clicked()
    app.quit()


list_friends_online = []
list_friends_offline = []
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_p2p = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
clients_p2p = []
clients = []

if __name__ == "__main__":
    buffer_size = 1000000*1024
    message_logs = []

    app = tkinter.Tk()
    app.title("Chat Application Client")
    app.resizable(False, False)

    main_frame = tkinter.Frame(app)
    main_frame.grid(row=0, column=0)

    first_row_frame = tkinter.Frame(main_frame)
    first_row_frame.pack(padx=10, pady=10)

    host_label = tkinter.Label(first_row_frame, text="Hostname: ")
    host_label.grid(row=0, column=0)

    host_text = tkinter.Entry(first_row_frame)
    host_text.grid(row=0, column=1)

    port_label = tkinter.Label(first_row_frame, text="Port: ")
    port_label.grid(row=0, column=2, padx=(10, 0))

    port_text = tkinter.Entry(first_row_frame)
    port_text.grid(row=0, column=3, padx=(0, 10))

    connect_button = tkinter.Button(first_row_frame, text="Connect", command=connect_clicked)
    connect_button.grid(row=0, column=4)

    second_row_frame = tkinter.Frame(main_frame)
    second_row_frame.pack(padx=10, pady=10)

    username_label = tkinter.Label(second_row_frame, text="Username: ")
    username_label.grid(row=0, column=0)

    username_text = tkinter.Entry(second_row_frame)
    username_text.grid(row=0, column=1)

    port_p2p_label = tkinter.Label(second_row_frame, text="Port P2P: ")
    port_p2p_label.grid(row=0, column=2, padx=(10, 0))

    port_p2p_text = tkinter.Entry(second_row_frame, width=15)
    port_p2p_text.grid(row=0, column=3, padx=(0, 10))

    disconnect_button = tkinter.Button(second_row_frame, text="Disconnect", command=disconnect_clicked)
    disconnect_button.grid(row=0, column=4)

    message_list = tkinter.Text(main_frame, width=55, height=20, state="disabled")
    message_list.pack(padx=10)

    third_row_frame = tkinter.Frame(main_frame)
    third_row_frame.pack(padx=10, pady=10)

    send_file_button = tkinter.Button(third_row_frame, text="Send File", command=send_file_clicked)
    send_file_button.grid(row=0, column=0)

    message_content = tkinter.StringVar()
    message_text = tkinter.Entry(third_row_frame, width=50, textvariable=message_content)
    message_text.grid(row=0, column=1, padx=10)

    send_button = tkinter.Button(third_row_frame, text="Send", command=send_clicked)
    send_button.grid(row=0, column=2)

    friend_frame = tkinter.Frame(app)
    friend_frame.grid(row=0, column=1, padx=(0, 10))

    friend_online_label = tkinter.Label(friend_frame, text="Friends online")
    friend_online_label.pack()

    friend_online_list = tkinter.Listbox(friend_frame, exportselection=False)
    friend_online_list.bind("<<ListboxSelect>>", on_select_online_friend)
    friend_online_list.pack()

    friend_offline_label = tkinter.Label(friend_frame, text="Friends offline")
    friend_offline_label.pack()

    friend_offline_list = tkinter.Text(friend_frame, width=15, height=10, state="disabled")
    friend_offline_list.pack()

    modify_friend_label = tkinter.Label(friend_frame, text="Modify friend")
    modify_friend_label.pack()

    modify_friend_content = tkinter.StringVar()
    modify_friend_text = tkinter.Entry(friend_frame, textvariable=modify_friend_content)
    modify_friend_text.pack()

    modify_friend_button = tkinter.Frame(friend_frame)
    modify_friend_button.pack(pady=10)

    add_friend_button = tkinter.Button(modify_friend_button, text="Add", command=add_friend_clicked)
    add_friend_button.grid(row=0, column=0, padx=(0, 10))

    delete_friend_button = tkinter.Button(modify_friend_button, text="Delete", command=delete_friend_clicked)
    delete_friend_button.grid(row=0, column=1)

    app.protocol("WM_DELETE_WINDOW", on_closing)

    app.mainloop()
