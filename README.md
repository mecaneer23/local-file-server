# Local Upload Server

This is a simple local file server, written with Flask.

## Screenshots

![computer screenshot](/static/computer.png)

![iphone screenshot](/static/iphone1.png)
![iphone screenshot](/static/iphone2.png)

## Installation

```bash
git clone https://github.com/mecaneer23/local-upload-server/
cd local-upload-server
pip install -r requirements.txt
```

## Running

```bash
python3 server.py
```

## Usage

### Web interface - recommended

1. Open this webpage on all devices.
2. Upload file(s) using the form.
3. Download file(s) onto other device(s) from the list.

### CLI - simplified examples

Replace `SERVER.IP:PORT` with the ip and port provided by the server

#### List files on the server

```bash
curl SERVER.IP:PORT
```

#### Download file

```bash
curl SERVER.IP:PORT/files/FILENAME -O
```

#### Upload file

```bash
curl -X POST SERVER.IP:PORT/upload -F "file=@/path/to/file"
```

#### Delete file

```bash
curl SERVER.IP:PORT/delete/FILENAME
```

Replace `FILENAME` with the file you want to delete
