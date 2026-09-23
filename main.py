import customtkinter as ctk
from gadgets import *
from onnx_detextion import *
from window_capture import WindowCapture
from bot_thread import *
from screen_marker import ScreenMarker
from hotkeys import GlobalHotkeys, VK_F8, VK_F9
import cv2
import sys
import os
import json
import glob

ROUTES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "routes")

#Move Albion Client to the corner of the screen

#Bot thread
go = Move()
go.start()

# Set custom theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.models = filter_models(get_files_in_folder())
        self.model = "rough_stone.onnx"
        self.is_cuda = len(sys.argv) > 1 and sys.argv[1] == "cuda"
        self.net = build_model(self.is_cuda, f"models/{self.model}")

        self.resolution = "1024x720"
        self.waiting_time = 3.5
        self.width, self.height = self.resolution.split('x')
        self.screen_center = [int(self.width)/2, int(self.height)/2]
        self.lock = threading.Lock()

        self.vision_status = "off"
        self.bot_status = "off"
        self.wincap = WindowCapture(None)

        self.class_ids, self.confidences, self.boxes, self.class_list, self.centers = [], [], [], [], []
        

        self.geometry("480x640")
        self.title("The Gatherer 2.0 - Wandering Eye")
        self.iconbitmap("wanderingeye.ico")

        self.protocol("WM_DELETE_WINDOW", self.on_close)


        def update_vision_status():
            self.vision_status = self.actions_frame.get_state1()
            print("Vision status updated to:", self.vision_status)


        def update_bot_status():
            self.bot_status = self.actions_frame.get_state2()
            print("Bot status updated to:", self.bot_status)
                

        def update_info():
            cv2.destroyAllWindows()
            self.actions_frame.reset_values()
            self.bot_status="off"
            self.vision_status="off"
            
            print(self.onnx_model_box.get_option())
            self.model = self.onnx_model_box.get_option()
            self.net = build_model(self.is_cuda, f"models/{self.model}")          
            print(f"Using: {self.model}")
            
            self.width, self.height = self.game_size_box.get_option().split('x')
            self.wincap = WindowCapture(None, width=int(self.width), height=int(self.height))
            print(f"Game resolution: {self.width}x{self.height}")
            
            self.waiting_time = float(self.waiting_time_frame.get_value())
            print(f"Waiting time: {self.waiting_time}\n")

            self.save_settings()

        

        #Creating Objects
        self.actions_frame = SwitchesFrame(self, name="Actions", text1="Display bot's vision", text2="Gather resources", command_name1 = update_vision_status, command_name2 = update_bot_status)
        self.game_size_box = DropdownFrame(self, name="Select Window Size", text="Game resolution", default="1024x720" , options=["1024x720","1280x720", "1280x1024", "1366x768", "1600x900", "1680x1050", "1920x1080"])
        self.onnx_model_box = DropdownFrame(self, name="Select detection model", text="Onnx model", default="rough_stone.onnx", options=self.models)
        self.update_info_button = ctk.CTkButton(self, text="Save changes", command=update_info)
        self.waiting_time_frame = SingleEntryFrame(self, header_name="EntryFrame1", name="Waiting Time", text="3.5", default=3.5)
        self.route_frame = RouteFrame(self, name="Route", text1="Record route", text2="Follow route",
                                      command_name1=self.set_record, command_name2=self.set_follow,
                                      clear_cmd=self.clear_route, save_cmd=self.save_route, load_cmd=self.load_route,
                                      restart_cmd=self.restart_route,
                                      route_names=self.list_routes(), select_cmd=self.load_route)
        

        #Drawing Objects
        self.actions_frame.grid(row=0, column=0, pady=12, padx=10)
        self.waiting_time_frame.grid(row=1, column=0, pady=12, padx=10)
        self.game_size_box.grid(row=0, column=1, pady=12, padx=10)
        self.onnx_model_box.grid(row=1, column=1, pady=12, padx=10)
        self.update_info_button.grid(row=2, column=0, padx=20, pady=10)
        self.route_frame.grid(row=3, column=0, columnspan=2, pady=12, padx=10)

        self.marker = ScreenMarker(0, 0, self.winfo_screenwidth(), self.winfo_screenheight())
        self.hotkeys = GlobalHotkeys()
        self.hotkeys_ok = self.hotkeys.start()
        if self.hotkeys_ok:
            print("[Hotkeys] Global F8/F9 hook installed")
        else:
            print("[Hotkeys] Falling back to key polling (F8/F9)")
        self.load_settings()



    def bot_gathering(self):
        if self.bot_status=="on":
            go.update(self.centers, True, self.waiting_time, self.screen_center)
        elif self.bot_status=="off":
            go.update([], False, self.waiting_time, self.screen_center)

    def save_route(self):
        name = self.route_frame.get_save_name()
        with open(os.path.join(ROUTES_DIR, f"{name}.json"), "w") as f:
            json.dump(ROUTE, f)
        self.route_frame.select_var.set(name)
        self.route_frame.set_route_names(self.list_routes())
        print(f"[Route] Saved {len(ROUTE)} waypoints as routes/{name}.json")

    def load_route(self, name=None):
        if name is None:
            name = self.route_frame.get_selected_route()
        path = os.path.join(ROUTES_DIR, f"{name}.json")
        if not os.path.exists(path):
            print(f"[Route] routes/{name}.json not found")
            return
        with open(path) as f:
            data = json.load(f)
        ROUTE.clear()
        ROUTE.extend(data)
        go.reset_route_state()
        print(f"[Route] Loaded {len(ROUTE)} waypoints from routes/{name}.json")

    def settings_path(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

    def save_settings(self):
        data = {"model": self.model,
                "resolution": f"{self.width}x{self.height}",
                "waiting_time": self.waiting_time}
        try:
            with open(self.settings_path(), "w") as f:
                json.dump(data, f, indent=2)
            print("[Settings] Saved")
        except Exception as e:
            print("Save settings error:", e)

    def load_settings(self):
        path = self.settings_path()
        if not os.path.exists(path):
            return
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception as e:
            print("Load settings error:", e)
            return

        model = data.get("model")
        if model in self.models:
            self.model = model
            self.onnx_model_box.combobox_var.set(model)
            self.onnx_model_box.option = model
            self.net = build_model(self.is_cuda, f"models/{model}")

        resolution = data.get("resolution")
        if resolution in ["1024x720", "1280x720", "1280x1024", "1366x768", "1600x900", "1680x1050", "1920x1080"]:
            self.resolution = resolution
            self.width, self.height = resolution.split('x')
            self.screen_center = [int(self.width) / 2, int(self.height) / 2]
            self.game_size_box.combobox_var.set(resolution)
            self.game_size_box.option = resolution
            self.wincap = WindowCapture(None, width=int(self.width), height=int(self.height))

        if data.get("waiting_time") is not None:
            self.waiting_time = float(data["waiting_time"])
            self.waiting_time_frame.entry.delete(0, "end")
            self.waiting_time_frame.entry.insert(0, str(data["waiting_time"]))

        print(f"[Settings] Loaded: model={self.model}, resolution={self.resolution}, wait={self.waiting_time}")

    def set_record(self):
        if self.route_frame.get_state1() == "on":
            go.recording = True
            go.lmb_was_down = False
            self.bot_status = "off"
            self.actions_frame.switch_var2.set("off")
            print("[Route] Recording started: left-click in the game to add waypoints (bot paused)")
        else:
            go.recording = False
            print(f"[Route] Recording stopped ({len(ROUTE)} waypoints)")

    def set_follow(self):
        if self.route_frame.get_state2() == "on":
            if len(ROUTE) == 0:
                print("[Route] No waypoints yet: record or load a route first")
                self.route_frame.switch_var2.set("off")
                return
            go.reset_route_state()
            go.follow = True
            print(f"[Route] Following route ({len(ROUTE)} waypoints) - turn on 'Gather resources' to run it")
        else:
            go.follow = False
            print("[Route] Route following off")

    def clear_route(self):
        ROUTE.clear()
        go.reset_route_state()
        print("[Route] Route cleared")

    def restart_route(self):
        if len(ROUTE) == 0:
            print("[Route] No waypoints: load or record a route first")
            return
        go.reset_route_state()
        print(f"[Route] Restarted from waypoint 1/{len(ROUTE)}")

    def save_route(self):
        with open(self.route_path(), "w") as f:
            json.dump(ROUTE, f)
        print(f"[Route] Saved {len(ROUTE)} waypoints to route.json")

    def load_route(self):
        path = self.route_path()
        if not os.path.exists(path):
            print("[Route] route.json not found")
            return
        with open(path) as f:
            data = json.load(f)
        ROUTE.clear()
        ROUTE.extend(data)
        go.route_i = 0
        go.gathering_at_waypoint = False
        print(f"[Route] Loaded {len(ROUTE)} waypoints")

    def toggle_bot(self):
        if self.bot_status == "on":
            self.bot_status = "off"
            self.actions_frame.switch_var2.set("off")
            go.update([], False, self.waiting_time, self.screen_center)
            print("[Hotkey] Bot paused (F8)")
        else:
            self.bot_status = "on"
            self.actions_frame.switch_var2.set("on")
            go.update(self.centers, True, self.waiting_time, self.screen_center)
            print("[Hotkey] Bot started (F8)")

    def check_hotkeys(self):
        try:
            if self.hotkeys_ok:
                while not self.hotkeys.events.empty():
                    code = self.hotkeys.events.get()
                    if code == VK_F8:
                        self.toggle_bot()
                    elif code == VK_F9:
                        print("[Hotkey] Stopping (F9)")
                        self.on_close()
            else:
                import win32api
                f8_down = win32api.GetAsyncKeyState(VK_F8) & 0x8000
                f9_down = win32api.GetAsyncKeyState(VK_F9) & 0x8000
                if f8_down and not getattr(self, "f8_was_down", False):
                    self.toggle_bot()
                if f9_down and not getattr(self, "f9_was_down", False):
                    print("[Hotkey] Stopping (F9)")
                    self.on_close()
                self.f8_was_down = f8_down
                self.f9_was_down = f9_down
        except Exception as e:
            print("Hotkey error:", e)
        self.after(40, self.check_hotkeys)

    def list_routes(self):
        os.makedirs(ROUTES_DIR, exist_ok=True)
        names = sorted(os.path.splitext(os.path.basename(p))[0]
                       for p in glob.glob(os.path.join(ROUTES_DIR, "*.json")))
        if not names:
            legacy = os.path.join(os.path.dirname(os.path.abspath(__file__)), "route.json")
            if os.path.exists(legacy):
                os.replace(legacy, os.path.join(ROUTES_DIR, "route.json"))
                names = ["route"]
                print("[Route] Migrated route.json to routes/route.json")
        return names

    def update_status(self):
        if go.recording:
            self.actions_frame.set_status("Recording", "orange")
        elif self.bot_status == "on" and go.follow and ROUTE:
            self.actions_frame.set_status(f"Route {go.route_i + 1}/{len(ROUTE)}", "green")
        elif self.bot_status == "on":
            self.actions_frame.set_status("Gathering", "green")
        elif go.follow or self.vision_status == "on":
            self.actions_frame.set_status("Paused", "red")
        else:
            self.actions_frame.set_status("Idle", "gray")

    def update_screenshot(self):
        self.route_frame.set_count(len(ROUTE))
        self.update_status()
        if go.follow and ROUTE:
            self.marker.draw(ROUTE, min(go.route_i, len(ROUTE) - 1))
        elif go.recording and ROUTE:
            self.marker.draw(ROUTE, len(ROUTE) - 1)
        else:
            self.marker.hide()
        #Avoid running inference if there are no actions activated
        if(self.vision_status == "on" or self.bot_status =="on"):
            self.screenshot = self.wincap.get_screenshot()
            self.class_ids, self.confidences, self.boxes, self.class_list = results_objects(self.screenshot, self.net, self.model)
            self.centers = get_center(self.boxes)
            self.frame = results_frame(self.screenshot, self.class_ids, self.confidences, self.boxes, self.class_list)
        
        if (self.vision_status == "on"):
            cv2.imshow("Computer Vision", self.frame)
            cv2.waitKey(1)
            self.after(100,self.update_screenshot)
            self.after(100,self.bot_gathering)
            
        elif self.vision_status == "off":
            cv2.destroyAllWindows()
            self.after(100,self.update_screenshot)
            self.after(100,self.bot_gathering)

            
            
    def on_close(self):
        print("Closing")
        go.stop()
        self.destroy()    



if __name__ == "__main__":

    app = App()
    app.after(100, app.update_screenshot)
    app.after(40, app.check_hotkeys)
    app.mainloop()
