
import time
import threading
from rich.console import Console
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel

console = Console()
layout = Layout()

layout.split_column(
    Layout(name="header", size=3),
    Layout(name="body"),
    Layout(name="footer", size=3)
)

layout["header"].update(Panel("Header"))
layout["footer"].update(Panel("Footer"))

tasks = ["S1", "S2", "S3"]
task_layouts = [Layout(name=t, size=10) for t in tasks]
layout["body"].split_column(*task_layouts)

# Initial render
for t in tasks:
    layout["body"][t].update(Panel(f"Waiting {t}...", title=t))

def worker(task_id):
    for i in range(20):
        time.sleep(0.2)
        # Update logic simulating ParallelStreamUI
        content = f"Line {i} for {task_id}\n" * 5
        panel = Panel(content, title=f"Active {task_id}")
        layout["body"][task_id].update(panel)

# Run Live
print("Starting Demo...")
with Live(layout, refresh_per_second=10, screen=False):
    threads = []
    for t in tasks:
        th = threading.Thread(target=worker, args=(t,))
        th.start()
        threads.append(th)
    
    for th in threads:
        th.join()

print("Done.")
