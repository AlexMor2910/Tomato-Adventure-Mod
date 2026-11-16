"""Small read-only mGBA GDB remote client. No memory/register-write packets."""
import json
import socket
import struct
import time


class RSP:
	def __init__(self, port=2345, log=None):
		self.socket = socket.create_connection(("127.0.0.1", port), timeout=5)
		self.socket.settimeout(5)
		self.log = log
		self.points = set()

	def record(self, direction, payload):
		if self.log:
			self.log.write(json.dumps(dict(time=time.time(), direction=direction, payload=payload)) + "\n")
			self.log.flush()

	def receive(self):
		while True:
			char = self.socket.recv(1)
			if not char:
				raise ConnectionError("Debugger disconnected")
			if char == b"$":
				break
		data = bytearray()
		while True:
			char = self.socket.recv(1)
			if char == b"#":
				break
			if not char:
				raise ConnectionError("Truncated debugger packet")
			data.extend(char)
		checksum = self.socket.recv(1) + self.socket.recv(1)
		if int(checksum, 16) != sum(data) % 256:
			raise RuntimeError("Debugger packet checksum mismatch")
		self.socket.sendall(b"+")
		payload = data.decode("ascii")
		self.record("receive", payload)
		return payload

	def command(self, command):
		# Address-setting c/s variants, software breaks, writes and arbitrary
		# monitor commands are intentionally absent from this client's interface.
		allowed = command in ("?", "g", "s", "c") or command.startswith(("m", "Z1,", "z1,", "Z2,", "z2,", "Z3,", "z3,", "Z4,", "z4,", "qSupported:"))
		if not allowed:
			raise ValueError("Command outside read-only debugger interface")
		self.record("send", command)
		data = command.encode("ascii")
		self.socket.sendall(b"$" + data + b"#" + f"{sum(data) % 256:02x}".encode())
		return self.receive()

	def registers(self):
		raw = bytes.fromhex(self.command("g"))
		if len(raw) != 68:
			raise RuntimeError(f"Unexpected mGBA 0.10.5 register packet length: {len(raw)}")
		values = struct.unpack("<17I", raw)
		return dict(zip([f"r{i}" for i in range(13)] + ["sp", "lr", "pc", "cpsr"], values))

	def memory(self, address, size):
		if not 0 < size <= 512:
			raise ValueError("mGBA memory packet must read 1..512 bytes")
		data = bytes.fromhex(self.command(f"m{address:x},{size:x}"))
		if len(data) != size:
			raise RuntimeError("Incomplete memory response")
		return data

	def point(self, kind, address, size=1, enabled=True):
		if kind not in (1, 2, 3, 4):
			raise ValueError("Use hardware execution or memory watchpoints")
		key = (kind, address, size)
		response = self.command(f"{'Z' if enabled else 'z'}{kind},{address:x},{size:x}")
		if response != "OK":
			raise RuntimeError(f"Point rejected: {response}")
		if enabled:
			self.points.add(key)
		else:
			self.points.discard(key)

	def close(self):
		try:
			for kind, address, size in list(self.points):
				self.point(kind, address, size, enabled=False)
		finally:
			self.socket.close()
