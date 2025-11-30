import os

template = """{% load static %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>__CODE__ | __TITLE__ - Villen</title>

    <style>
        body {
            margin: 0;
            background: #0a0a0d;
            color: #fff;
            font-family: "Poppins", sans-serif;
            overflow: hidden;
        }

        .matrix {
            position: fixed;
            top: 0; 
            left: 0;
            width: 100%;
            height: 100%;
            opacity: 0.15;
            z-index: -1;
        }

        .container {
            height: 80vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
            text-align: center;
            padding: 0 20px;
        }

        h1 {
            font-size: 5rem;
            font-weight: 700;
            margin: 0;
            color: #ff4444;
            text-shadow: 0 0 25px #ff4444;
            animation: glitch 1.5s infinite;
        }

        @keyframes glitch {
            0% { text-shadow: 2px 2px #ff0000; }
            25% { text-shadow: -2px -2px #ff4444; }
            50% { text-shadow: 2px -2px #ff0000; }
            75% { text-shadow: -2px 2px #ff4444; }
            100% { text-shadow: 2px 2px #ff0000; }
        }

        p {
            font-size: 1.2rem;
            margin: 25px 0;
            opacity: 0.8;
        }

        .btn {
            display: inline-block;
            padding: 12px 28px;
            background: #11ff88;
            color: #000;
            text-decoration: none;
            border-radius: 10px;
            font-weight: 600;
            box-shadow: 0 0 15px #11ff88;
            transition: 0.3s ease-in-out;
        }

        .btn:hover {
            background: #0f0;
            transform: translateY(-4px);
            box-shadow: 0 0 25px #0f0;
        }

        .bottom {
            margin-top: 40px;
        }
    </style>
</head>

<body>

    <canvas class="matrix"></canvas>

    <div class="container">
        <h1>__CODE__</h1>
        <p>__MESSAGE__</p>
        <p>__SUB_MESSAGE__</p>
    </div>

    <div class="bottom">
        <a href="{% url 'core:home' %}" class="btn">Return to Home</a>
    </div>

    <script>
        // Matrix Animation
        const canvas = document.querySelector(".matrix");
        const ctx = canvas.getContext("2d");

        canvas.height = window.innerHeight;
        canvas.width = window.innerWidth;

        const chars = "01";
        const fontSize = 16;
        const columns = canvas.width / fontSize;
        const drops = Array(Math.floor(columns)).fill(1);

        function draw() {
            ctx.fillStyle = "rgba(0, 0, 0, 0.05)";
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            ctx.fillStyle = "#11ff88";
            ctx.font = fontSize + "px monospace";

            drops.forEach((y, index) => {
                const txt = chars[Math.floor(Math.random() * chars.length)];
                ctx.fillText(txt, index * fontSize, y * fontSize);

                if (y * fontSize > canvas.height && Math.random() > 0.975)
                    drops[index] = 0;
                drops[index]++;
            });
        }

        setInterval(draw, 33);
        
        window.addEventListener('resize', () => {
             canvas.height = window.innerHeight;
             canvas.width = window.innerWidth;
        });
    </script>

</body>
</html>
"""

pages = [
    ("400", "Bad Request", "Bad Request", "Your browser sent a request that this server could not understand."),
    ("401", "Unauthorized", "Access Denied", "You are not authorized to access this page."),
    ("403", "Forbidden", "Forbidden", "You don't have permission to access this resource."),
    ("408", "Request Timeout", "Request Timeout", "The server timed out waiting for the request."),
    ("429", "Too Many Requests", "Too Many Requests", "You are being rate limited. Chill out."),
    ("502", "Bad Gateway", "Bad Gateway", "The server received an invalid response from the upstream server."),
    ("503", "Service Unavailable", "Service Unavailable", "The server is currently unavailable (overloaded or down for maintenance)."),
    ("504", "Gateway Timeout", "Gateway Timeout", "The upstream server failed to send a request in the time allowed."),
]

base_dir = "core/templates/core"
if not os.path.exists(base_dir):
    os.makedirs(base_dir)

for code, title, message, sub_message in pages:
    content = template.replace("__CODE__", code).replace("__TITLE__", title).replace("__MESSAGE__", message).replace("__SUB_MESSAGE__", sub_message)
    with open(os.path.join(base_dir, f"{code}.html"), "w") as f:
        f.write(content)
    print(f"Created {code}.html")
