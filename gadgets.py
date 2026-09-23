import customtkinter as ctk
import tkinter

def if_empty(value, default):
    if(value == ""):
        value = float(default)
    else:
        pass
    return value


class SwitchesFrame(ctk.CTkFrame):
    def __init__(self, *args, header_name="TestFrame", name, text1, text2, command_name1, command_name2 , **kwargs):
        super().__init__(*args, **kwargs)


        # Add a label to the new entry frame
        self.label1 = ctk.CTkLabel(self, text=name, anchor="center")
        self.label1.grid(row=0, column=0, columnspan=3, pady=(10, 0), padx=10, sticky="n")

        # Add two entries to the new entry frame
        self.switch_var1 = ctk.StringVar(value="off")
        self.switch1 = ctk.CTkSwitch(self, text=text1, variable=self.switch_var1, onvalue="on", offvalue="off", command=command_name1)
        self.switch1.grid(row=1, column=0, pady=12, padx=10)

        self.switch_var2 = ctk.StringVar(value="off")
        self.switch2 = ctk.CTkSwitch(self, text=text2, variable=self.switch_var2, onvalue="on", offvalue="off", command=command_name2)
        self.switch2.grid(row=2, column=0, pady=12, padx=10)

        # Always-visible bot state, to the right of the switches
        self.status_dot = ctk.CTkLabel(self, text="●", text_color="gray", font=ctk.CTkFont(size=22))
        self.status_dot.grid(row=1, column=1, rowspan=2, padx=(4, 2))
        self.status_text = ctk.CTkLabel(self, text="Idle", text_color="gray", anchor="w", width=80)
        self.status_text.grid(row=1, column=2, rowspan=2, padx=(0, 12))


    def get_state1(self):
        """ returns on or off"""
        return self.switch_var1.get()

    def get_state2(self):
        """ returns on or off"""
        return self.switch_var2.get()

    def set_status(self, text, color):
        self.status_dot.configure(text_color=color)
        self.status_text.configure(text=text, text_color=color)

    def reset_values(self):
        self.switch1.deselect()
        self.switch2.deselect()



class DoubleEntryFrame(ctk.CTkFrame):
    def __init__(self, *args, header_name="TestFrame", name, text1, text2, default1, default2, **kwargs):
        super().__init__(*args, **kwargs)

        self.default1 = default1
        self.default2 = default2

        # Add a label to the new entry frame
        self.label1 = ctk.CTkLabel(self, text=name, anchor="center")
        self.label1.grid(row=0, column=0, columnspan=2, pady=(10, 0), padx=10, sticky="n")

        # Define the validation function to allow only integers
        validate_int = (self.register(self._validate_int), '%P')

        # Add two entries to the new entry frame
        self.entry1 = ctk.CTkEntry(self, width=50, placeholder_text=text1, validate="key", validatecommand=validate_int)
        self.entry1.grid(row=1, column=0, pady=12, padx=1)

        self.entry2 = ctk.CTkEntry(self, width=50, placeholder_text=text2, validate="key", validatecommand=validate_int)
        self.entry2.grid(row=1, column=1, pady=12, padx=10)

    def _validate_int(self, value):
        """Validate that the input value is an integer."""
        if not value:
            return True

        try:
            int(value)
            return True
        except ValueError:
            return False

    def get_value1(self):
        """ returns selected value as a string, returns an empty string if nothing selected """
        self.value1 = if_empty(self.entry1.get(), self.default1)
        return self.value1

    def get_value2(self):
        """ returns selected value as a string, returns an empty string if nothing selected """

        self.value2 = if_empty(self.entry2.get(), self.default2)
        return self.value2


class SingleEntryFrame(ctk.CTkFrame):
    def __init__(self, *args, header_name="TestFrame", name, text, default, **kwargs):
        super().__init__(*args, **kwargs)
        self.default = default
        # Add a label to the new entry frame
        self.label1 = ctk.CTkLabel(self, text=name, anchor="center")
        self.label1.grid(row=0, column=0, columnspan=2, pady=(10, 0), padx=10, sticky="n")

        # Define the validation function to allow only integers
        validate_int = (self.register(self._validate_int), '%P')

        # Add a single entry to the new entry frame
        self.entry = ctk.CTkEntry(self, width=50, placeholder_text=text, validate="key", validatecommand=validate_int)
        self.entry.grid(row=1, column=0, pady=12, padx=1)

    def _validate_int(self, value):
        """Validate that the input value is an integer."""
        if not value:
            return True

        try:
            float(value)
            return True
        except ValueError:
            return False

    def get_value(self):
        """ returns selected value as a string, returns an empty string if nothing selected """
        self.value = if_empty(self.entry.get(), self.default)
        return self.value


class DropdownFrame(ctk.CTkFrame):
    def __init__(self, *args, header_name="TestFrame", name, text, default, options, **kwargs):
        super().__init__(*args, **kwargs)


        # Add a label to the new entry frame
        self.label1 = ctk.CTkLabel(self, text=name, anchor="center")
        self.label1.grid(row=0, column=0, columnspan=1, pady=(10, 0), padx=10, sticky="n")

        self.combobox_var = ctk.StringVar(value=text)  # set initial value
        self.option = ""
        self.default = default

        def combobox_callback(choice):
            #print(f"{text}:", choice)
            self.option = choice


        #["800 x 600", "1024 x 768", "1280 x 720", "1280 x 1024", "1366 x 768", "1600 x 900", "1680 x 1050", "1920 x 1080"]

        self.combobox = ctk.CTkComboBox(self, values=options, command=combobox_callback, variable=self.combobox_var)
        self.combobox.grid(row=1, column=0, pady=12, padx=10)


    def get_option(self):
        if self.option == "":
            self.option = self.default
        return self.option


class ModelsFrame(ctk.CTkFrame):
    def __init__(self, *args, name, models, selected=None, **kwargs):
        super().__init__(*args, **kwargs)

        selected = selected or []
        self.label1 = ctk.CTkLabel(self, text=name, anchor="center")
        self.label1.grid(row=0, column=0, pady=(10, 4), padx=10, sticky="n")

        # "Select all / None" quick toggles for a long model list
        all_button = ctk.CTkButton(self, text="All", width=45, command=lambda: self.set_all(True))
        all_button.grid(row=1, column=0, padx=(4, 2), pady=(0, 4), sticky="w")
        none_button = ctk.CTkButton(self, text="None", width=45, command=lambda: self.set_all(False))
        none_button.grid(row=1, column=1, padx=(2, 4), pady=(0, 4), sticky="w")

        self.vars = {}
        row = 2
        for model in models:
            var = ctk.StringVar(value="1" if model in selected else "0")
            ctk.CTkCheckBox(self, text=model, variable=var, onvalue="1", offvalue="0") \
                .grid(row=row, column=0, columnspan=2, pady=1, padx=12, sticky="w")
            self.vars[model] = var
            row += 1

        self.note = ctk.CTkLabel(self, text="Tick models, then Save changes",
                                 text_color="gray", anchor="center")
        self.note.grid(row=row, column=0, columnspan=2, pady=(6, 10), padx=10)

    def get_selected(self):
        return [model for model, var in self.vars.items() if var.get() == "1"]

    def set_selected(self, models):
        for model, var in self.vars.items():
            var.set("1" if model in models else "0")

    def set_all(self, state):
        value = "1" if state else "0"
        for var in self.vars.values():
            var.set(value)


class RouteFrame(ctk.CTkFrame):
    def __init__(self, *args, name, text1, text2, command_name1, command_name2,
                 clear_cmd, save_cmd, load_cmd, restart_cmd=None,
                 route_names=None, select_cmd=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.label1 = ctk.CTkLabel(self, text=name, anchor="center")
        self.label1.grid(row=0, column=0, columnspan=3, pady=(10, 0), padx=10, sticky="n")

        self.switch_var1 = ctk.StringVar(value="off")
        self.switch1 = ctk.CTkSwitch(self, text=text1, variable=self.switch_var1,
                                     onvalue="on", offvalue="off", command=command_name1)
        self.switch1.grid(row=1, column=0, columnspan=2, pady=(6, 0), padx=10, sticky="w")

        self.switch_var2 = ctk.StringVar(value="off")
        self.switch2 = ctk.CTkSwitch(self, text=text2, variable=self.switch_var2,
                                     onvalue="on", offvalue="off", command=command_name2)
        self.switch2.grid(row=1, column=2, pady=(6, 0), padx=10, sticky="w")

        self.count_label = ctk.CTkLabel(self, text="Waypoints: 0", anchor="center")
        self.count_label.grid(row=2, column=0, columnspan=3, pady=(6, 0), padx=10)
        self._shown_count = 0

        self.clear_button = ctk.CTkButton(self, text="Clear", width=70, command=clear_cmd)
        self.clear_button.grid(row=3, column=0, pady=(6, 10), padx=4)

        self.save_button = ctk.CTkButton(self, text="Save", width=70, command=save_cmd)
        self.save_button.grid(row=3, column=1, pady=(6, 10), padx=4)

        self.load_button = ctk.CTkButton(self, text="Load", width=70, command=load_cmd)
        self.load_button.grid(row=3, column=2, pady=(6, 10), padx=4)

        # Saved-routes selector, to the right of the route menu
        self.route_label = ctk.CTkLabel(self, text="Route:", anchor="w")
        self.route_label.grid(row=4, column=0, pady=(6, 10), padx=(10, 2), sticky="w")
        self.select_var = ctk.StringVar(value=route_names[0] if route_names else "route")

        def on_select(choice):
            if select_cmd:
                select_cmd(choice)

        self.route_combo = ctk.CTkComboBox(self, values=route_names or ["route"],
                                           command=on_select, variable=self.select_var, width=185)
        self.route_combo.grid(row=4, column=1, columnspan=2, pady=(6, 10), padx=4, sticky="w")

        # Simple save: type a name next to Save and store the route under it
        self.save_label = ctk.CTkLabel(self, text="Save as:", anchor="w")
        self.save_label.grid(row=5, column=0, pady=(0, 10), padx=(10, 2), sticky="w")
        self.save_name_var = ctk.StringVar(value=route_names[0] if route_names else "route")
        self.name_entry = ctk.CTkEntry(self, textvariable=self.save_name_var, width=185,
                                       placeholder_text="route name")
        self.name_entry.grid(row=5, column=1, columnspan=2, pady=(0, 10), padx=4, sticky="w")
        self.name_entry.bind("<Return>", lambda e: save_cmd())

        self.restart_button = ctk.CTkButton(self, text="Restart route", width=150, command=restart_cmd)
        self.restart_button.grid(row=6, column=0, columnspan=3, pady=(0, 10), padx=4)

    def get_state1(self):
        return self.switch_var1.get()

    def get_state2(self):
        return self.switch_var2.get()

    def get_selected_route(self):
        name = self.select_var.get()
        return name if name else "route"

    def get_save_name(self):
        name = self.save_name_var.get().strip()
        return name if name else "route"

    def set_route_names(self, names):
        cur = self.select_var.get()
        if cur and cur not in names:
            names = [cur] + list(names)
        self.route_combo.configure(values=names)
        self.select_var.set(cur if cur else (names[0] if names else "route"))

    def set_count(self, count):
        if count != self._shown_count:
            self._shown_count = count
            self.count_label.configure(text=f"Waypoints: {count}")
