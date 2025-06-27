import tkinter as tk
from tkinter import messagebox
from PIL import ImageGrab
import io
import win32clipboard
import requests
import tempfile
import webbrowser

class ScreenshotApp:
    def __init__(self, root):
        self.root = root
        self.root.overrideredirect(True)
        self.root.attributes('-alpha', 0.1)
        self.root.attributes('-topmost', True)
        
        screen_size = f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0"
        self.root.geometry(screen_size)
        
        self.root.bind('<Escape>', lambda e: self.root.destroy())
        
        self.start_x = None
        self.start_y = None
        self.current_x = None
        self.current_y = None
        self.dragging = False 

        self.canvas = tk.Canvas(root, cursor="cross", bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)

        self.create_static_gradient()
        
        self.label = tk.Label(root, text="Click and drag to select region (Press ESC to cancel)", 
                            bg='black', fg='white', font=('Arial', 16))
        self.label.place(relx=0.5, rely=0.8, anchor=tk.CENTER)
        
        self.root.withdraw()
        self.root.update()
        self.reference_screenshot = ImageGrab.grab()
        self.root.deiconify()

    def create_static_gradient(self):
        width = self.root.winfo_screenwidth()
        height = self.root.winfo_screenheight()
        
        self.gradient_img = tk.PhotoImage(width=width, height=height)
        
        for y in range(height):
            g = int(255 * (y / height))
            color = f"#ff{g:02x}00"
            self.gradient_img.put(color, (0, y, width, y+1))
        
        self.canvas.create_image(0, 0, image=self.gradient_img, anchor=tk.NW, tags="gradient")

    def on_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.dragging = False
        self.rect = self.canvas.create_rectangle(
            self.start_x, self.start_y, 
            self.start_x, self.start_y,
            outline='red', width=2, fill='white')
        self.canvas.tag_raise(self.rect)

    def on_drag(self, event):
        self.dragging = True
        self.current_x, self.current_y = (event.x, event.y)
        self.canvas.coords(
            self.rect, self.start_x, self.start_y,
            self.current_x, self.current_y)

    def on_release(self, event):
        if self.dragging:
            self.root.withdraw()
            self.root.update()
            self.capture_region()
        self.root.destroy()

    def catbox(self, image):
        try:
            temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
            image.save(temp_file.name, 'PNG')
            temp_file.close()
            
            imageJson = {
                'reqtype': (None, 'fileupload'),
                'time': (None, '24h'),
                'fileToUpload': (temp_file.name, open(temp_file.name, 'rb'), 'image/png')
            }
            
            response = requests.post(
                'https://litterbox.catbox.moe/resources/internals/api.php',
                files=imageJson
            )
            
            if response.status_code == 200 and response.text.startswith('http'):
                return response.text.strip()
            return None
        except Exception as e:
            print(f"Error uploading to Litterbox: {e}")
            return None

    def capture_region(self):
        x1 = min(self.start_x, self.current_x)
        y1 = min(self.start_y, self.current_y)
        x2 = max(self.start_x, self.current_x)
        y2 = max(self.start_y, self.current_y)
        
        if abs(x2 - x1) > 10 and abs(y2 - y1) > 10:
            screen_x1 = x1 + self.root.winfo_x()
            screen_y1 = y1 + self.root.winfo_y()
            screen_x2 = x2 + self.root.winfo_x()
            screen_y2 = y2 + self.root.winfo_y()
            
            screenshot = ImageGrab.grab(bbox=(screen_x1, screen_y1, screen_x2, screen_y2))
            
            output = io.BytesIO()
            screenshot.convert("RGB").save(output, format="BMP")
            data = output.getvalue()[14:]
            output.close()
            
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
            
            litter = self.catbox(screenshot)
            if litter is not None:
                webbrowser.open(f'https://lens.google.com/uploadbyurl?url={litter}')
            else:
                messagebox.showerror("Error", "Upload failed - paste the image in Google Lens later :)")
                webbrowser.open('https://lens.google.com')
        else:
            raise SystemExit(1)

if __name__ == "__main__":
    root = tk.Tk()
    app = ScreenshotApp(root)
    root.mainloop()