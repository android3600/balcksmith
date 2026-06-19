import http from "node:http";
import fs from "node:fs";
import path from "node:path";

const root = path.resolve(process.cwd());
const port = Number(process.env.PORT || 8010);
const types = {
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".webp": "image/webp",
  ".jpg": "image/jpeg",
  ".png": "image/png",
};

http.createServer((req, res) => {
  const urlPath = decodeURIComponent((req.url || "/").split("?")[0]);
  const rel = urlPath === "/" ? "blacksmith.html" : urlPath.replace(/^\/+/, "");
  const file = path.resolve(root, rel);
  if (!file.startsWith(root)) {
    res.writeHead(403);
    res.end("Forbidden");
    return;
  }
  fs.readFile(file, (err, data) => {
    if (err) {
      res.writeHead(404);
      res.end("Not found");
      return;
    }
    res.writeHead(200, { "Content-Type": types[path.extname(file)] || "application/octet-stream" });
    res.end(data);
  });
}).listen(port, "127.0.0.1");
