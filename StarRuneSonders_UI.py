import os
import sys
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

BASE_DIR = Path(__file__).resolve().parent
COMPILER_PATH = BASE_DIR / 'StarRuneSonders.py'
IMAGE_DIR = BASE_DIR / 'images'
ASSET_DIR = BASE_DIR / 'star_assets'


def load_compiler_module():
    spec = spec_from_file_location('StarRuneSonders_core', COMPILER_PATH)
    if spec is None or spec.loader is None:
        raise FileNotFoundError(f'Could not load compiler file at {COMPILER_PATH}')
    module = module_from_spec(spec)
    sys.modules['StarRuneSonders_core'] = module
    spec.loader.exec_module(module)
    return module


core = load_compiler_module()


class StarRuneSondersUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title('StarRuneSonders : By Capili, Tomas')
        self.root.state('zoomed')
        self.root.minsize(1200, 700)
        self.root.configure(bg='#111111')

        self.compiler = core
        self.photo_images = {}
        self.current_scene_key = 'intro'
        self.story_stage = 0
        self.last_output = ''

        self.scene_map = {
            'intro': {
                'title': 'Forest Dusk',
                'text': 'You fall through a hidden trap in the forest and wake inside a quiet cabin that feels preserved by grief.',
                'asset': 'intro.png'
            },
            'wakeup': {
                'title': 'Cabin Awakening',
                'text': 'A stranger silence sits in the room. The bed, lamp, and still air make it feel like time has stopped.',
                'asset': 'wakeup.png'
            },
            'photo': {
                'title': 'Faded Photograph',
                'text': 'A mother and daughter stand outside this same cabin. The memory feels warm, but unfinished.',
                'asset': 'photo.png'
            },
            'note': {
                'title': 'Folded Note',
                'text': 'The note gently points toward what mattered most in the room, as if someone expected you to understand.',
                'asset': 'note.png'
            },
            'framekey': {
                'title': 'Hidden Key',
                'text': 'Behind the photograph frame rests a small key, tucked away like a truth that was not ready to be spoken.',
                'asset': 'framekey.png'
            },
            'drawer': {
                'title': 'Locked Drawer',
                'text': 'The drawer resists until memory recognizes that you truly noticed the frame and what it concealed.',
                'asset': 'drawer.png'
            },
            'letters': {
                'title': 'Unread Letters',
                'text': 'Inside are letters written by a grieving mother to a daughter who is already gone.',
                'asset': 'letters.png'
            },
            'truth': {
                'title': 'The Truth',
                'text': 'This was never only a puzzle. It is a place where memory and loss were kept alive on purpose.',
                'asset': 'truth.png'
            },
            'grief': {
                'title': 'Memorial House',
                'text': 'The cabin is grief preserved into architecture — not horror, but love refusing to disappear.',
                'asset': 'grief.png'
            },
            'all': {
                'title': 'Everything Revealed',
                'text': 'Every clue aligns. The cabin is understood at last as a memorial built by love and mourning.',
                'asset': 'all.png'
            }
        }

        self.story_beats = [
            ('intro', 'Dusk breaks under your feet. You fall into the forest trap before you can even scream.'),
            ('wakeup', 'When you wake, it is not pain you notice first — it is how quiet the cabin is.'),
            ('photo', 'A photograph sits nearby, not hidden, but waiting to be looked at properly.'),
            ('note', 'There is also a note, folded with the kind of care people use for the things they cannot bear to lose.'),
            ('framekey', 'Some memories are direct. Others stay hidden behind frames until someone finally pays attention.'),
            ('drawer', 'A locked drawer waits in the room, stubborn in the way grief often is.'),
            ('letters', 'If it opens, it will not reveal treasure. It will reveal what somebody could never throw away.'),
            ('truth', 'And somewhere past all that silence is the real reason this house still remembers.'),
        ]

        self._build_style()
        self._build_layout()
        self._load_scene('intro')
        self._show_intro_text()

    def _build_style(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass

        style.configure('Main.TFrame', background='#111111')
        style.configure('Card.TFrame', background='#1b1a19')
        style.configure('Panel.TFrame', background='#161514')
        style.configure('Title.TLabel', background='#111111', foreground='#f1eadf', font=('Georgia', 22, 'bold'))
        style.configure('Sub.TLabel', background='#111111', foreground='#c7bba8', font=('Segoe UI', 10))
        style.configure('SceneTitle.TLabel', background='#1b1a19', foreground='#f3e7d5', font=('Georgia', 16, 'bold'))
        style.configure('Section.TLabel', background='#161514', foreground='#f0e3cf', font=('Segoe UI', 10, 'bold'))
        style.configure('Body.TLabel', background='#1b1a19', foreground='#ddd4c7', font=('Segoe UI', 11), wraplength=430)
        style.configure('Muted.TLabel', background='#161514', foreground='#bba98f', font=('Segoe UI', 9))
        style.configure('Action.TButton', font=('Segoe UI', 10, 'bold'))

    def _build_layout(self):
        outer = ttk.Frame(self.root, style='Main.TFrame', padding=18)
        outer.pack(fill='both', expand=True)
        outer.columnconfigure(0, weight=11)
        outer.columnconfigure(1, weight=9)
        outer.rowconfigure(1, weight=1)

        header = ttk.Frame(outer, style='Main.TFrame')
        header.grid(row=0, column=0, columnspan=2, sticky='ew', pady=(0, 14))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text='StarRuneSonders', style='Title.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(
            header,
            text='A front-end where each line uncovers memory and grief.',
            style='Sub.TLabel'
        ).grid(row=1, column=0, sticky='w', pady=(4, 0))

        left = ttk.Frame(outer, style='Card.TFrame', padding=14)
        left.grid(row=1, column=0, sticky='nsew', padx=(0, 10))
        left.columnconfigure(0, weight=1)
        left.rowconfigure(1, weight=1)

        left_top = ttk.Frame(left, style='Card.TFrame')
        left_top.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        left_top.columnconfigure(0, weight=1)
        left_top.columnconfigure(1, weight=0)

        ttk.Label(left_top, text='Scene Viewer', style='SceneTitle.TLabel').grid(row=0, column=0, sticky='w')
        self.scene_badge_var = tk.StringVar(value='STAGE 01  •  FOREST DUSK')
        tk.Label(
            left_top,
            textvariable=self.scene_badge_var,
            bg='#2b241e',
            fg='#ead7bf',
            font=('Consolas', 9, 'bold'),
            padx=10,
            pady=5
        ).grid(row=0, column=1, sticky='e')

        image_wrap = tk.Frame(left, bg='#141312', highlightbackground='#3a322a', highlightthickness=1)
        image_wrap.grid(row=1, column=0, sticky='nsew')
        image_wrap.rowconfigure(0, weight=1)
        image_wrap.columnconfigure(0, weight=1)

        self.image_label = tk.Label(
            image_wrap,
            bg='#141312',
            fg='#f2e4cf',
            font=('Georgia', 16, 'bold'),
            justify='center',
            wraplength=500,
            text='Scene image will appear here'
        )
        self.image_label.grid(row=0, column=0, sticky='nsew', padx=10, pady=10)

        scene_panel = ttk.Frame(left, style='Panel.TFrame', padding=12)
        scene_panel.grid(row=2, column=0, sticky='ew', pady=(12, 0))
        scene_panel.columnconfigure(0, weight=1)

        ttk.Label(scene_panel, text='Current Memory', style='Section.TLabel').grid(row=0, column=0, sticky='w')
        self.scene_title_var = tk.StringVar(value='Forest Dusk')
        self.scene_text_var = tk.StringVar(value='')
        ttk.Label(scene_panel, textvariable=self.scene_title_var, style='SceneTitle.TLabel').grid(row=1, column=0, sticky='w', pady=(6, 4))
        ttk.Label(scene_panel, textvariable=self.scene_text_var, style='Body.TLabel').grid(row=2, column=0, sticky='w')

        right = ttk.Frame(outer, style='Card.TFrame', padding=14)
        right.grid(row=1, column=1, sticky='nsew')
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=5)
        right.rowconfigure(2, weight=6)

        story_panel = ttk.Frame(right, style='Panel.TFrame', padding=10)
        story_panel.grid(row=0, column=0, sticky='nsew')
        story_panel.columnconfigure(0, weight=1)
        story_panel.rowconfigure(1, weight=1)

        ttk.Label(story_panel, text='Story Feed', style='Section.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(story_panel, text='What the cabin is telling you', style='Muted.TLabel').grid(row=0, column=1, sticky='e')

        self.story_text = ScrolledText(
            story_panel,
            height=12,
            bg='#121110',
            fg='#e7dccd',
            insertbackground='#f5e6cf',
            relief='flat',
            wrap='word',
            font=('Consolas', 10)
        )
        self.story_text.grid(row=1, column=0, columnspan=2, sticky='nsew', pady=(8, 0))
        self.story_text.configure(state='disabled')

        button_row = ttk.Frame(right, style='Card.TFrame')
        button_row.grid(row=1, column=0, sticky='ew', pady=(12, 12))
        button_row.columnconfigure((0, 1, 2), weight=1)

        ttk.Button(button_row, text='Continue Story', style='Action.TButton', command=self.advance_story).grid(row=0, column=0, sticky='ew', padx=(0, 6))
        ttk.Button(button_row, text='Reveal All', style='Action.TButton', command=lambda: self.run_line('reveal:all.')).grid(row=0, column=1, sticky='ew', padx=6)
        ttk.Button(button_row, text='Reset Memory', style='Action.TButton', command=self.reset_memory).grid(row=0, column=2, sticky='ew', padx=(6, 0))

        terminal_panel = ttk.Frame(right, style='Panel.TFrame', padding=10)
        terminal_panel.grid(row=2, column=0, sticky='nsew')
        terminal_panel.columnconfigure(0, weight=1)
        terminal_panel.rowconfigure(1, weight=1)

        ttk.Label(terminal_panel, text='Console', style='Section.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(terminal_panel, text='Enter one StarRuneSonders line at a time', style='Muted.TLabel').grid(row=0, column=1, sticky='e')

        self.terminal_output = ScrolledText(
            terminal_panel,
            height=16,
            bg='#0e0e0e',
            fg='#d6d6d6',
            insertbackground='#ffffff',
            relief='flat',
            wrap='word',
            font=('Consolas', 10)
        )
        self.terminal_output.grid(row=1, column=0, columnspan=2, sticky='nsew', pady=(8, 0))
        self.terminal_output.configure(state='disabled')

        entry_row = ttk.Frame(right, style='Card.TFrame')
        entry_row.grid(row=3, column=0, sticky='ew', pady=(12, 0))
        entry_row.columnconfigure(0, weight=1)

        self.command_var = tk.StringVar()
        self.command_entry = tk.Entry(
            entry_row,
            textvariable=self.command_var,
            bg='#161616',
            fg='#f1eadf',
            insertbackground='#ffffff',
            relief='flat',
            font=('Consolas', 11)
        )
        self.command_entry.grid(row=0, column=0, sticky='ew', ipady=8)
        self.command_entry.bind('<Return>', lambda event: self.submit_command())

        tk.Button(
            entry_row,
            text='Run',
            command=self.submit_command,
            bg='#5d4633',
            fg='white',
            activebackground='#72563f',
            activeforeground='white',
            relief='flat',
            padx=16,
            pady=8
        ).grid(row=0, column=1, padx=(8, 0))

        helper_panel = ttk.Frame(right, style='Panel.TFrame', padding=10)
        helper_panel.grid(row=4, column=0, sticky='ew', pady=(12, 0))
        helper_panel.columnconfigure(0, weight=1)
        ttk.Label(helper_panel, text='Reference', style='Section.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Label(helper_panel, text='Refer to cheat sheet for valid commands and test cases.', style='Body.TLabel').grid(row=1, column=0, sticky='w', pady=(6, 0))

    def _append_story(self, text: str):
        self.story_text.configure(state='normal')
        self.story_text.insert('end', text + '\n\n')
        self.story_text.see('end')
        self.story_text.configure(state='disabled')

    def _append_terminal(self, text: str):
        self.terminal_output.configure(state='normal')
        self.terminal_output.insert('end', text + '\n')
        self.terminal_output.see('end')
        self.terminal_output.configure(state='disabled')

    def _show_intro_text(self):
        intro = (
            'The traveler falls into a hidden trap in the forest at dusk and wakes inside a cabin that feels too careful to be abandoned. '
            'Nothing here is random. The photograph, the note, the locked drawer, and the letters all point toward a mother, a daughter, and a grief that never truly left.'
        )
        self._append_story(intro)
        self._append_terminal('Story mode ready. Enter one StarRuneSonders line at a time.')

    def _scene_asset_path(self, asset_name: str) -> Path:
        image_path = IMAGE_DIR / asset_name
        if image_path.exists():
            return image_path
        return ASSET_DIR / asset_name

    def _load_scene(self, key: str):
        scene = self.scene_map.get(key, self.scene_map['intro'])
        self.current_scene_key = key
        self.scene_title_var.set(scene['title'])
        self.scene_text_var.set(scene['text'])
        stage_map = {
            'intro': 'STAGE 01  •  FOREST DUSK',
            'wakeup': 'STAGE 02  •  CABIN AWAKENING',
            'photo': 'STAGE 03  •  PHOTOGRAPH',
            'note': 'STAGE 04  •  NOTE',
            'framekey': 'STAGE 05  •  HIDDEN KEY',
            'drawer': 'STAGE 06  •  DRAWER',
            'letters': 'STAGE 07  •  LETTERS',
            'truth': 'STAGE 08  •  TRUTH',
            'grief': 'STAGE 09  •  GRIEF',
            'all': 'FINAL  •  EVERYTHING REVEALED'
        }
        self.scene_badge_var.set(stage_map.get(key, 'MEMORY  •  UNKNOWN'))

        asset_path = self._scene_asset_path(scene['asset'])
        if asset_path.exists():
            try:
                img = tk.PhotoImage(file=str(asset_path))
                self.photo_images[key] = img
                self.image_label.configure(image=img, text='')
                self.image_label.image = img
                return
            except tk.TclError:
                pass

        placeholder = f"{scene['title']}\n\n{scene['text']}\n\n(Add an image later as: {asset_path.name})"
        self.image_label.configure(image='', text=placeholder)
        self.image_label.image = None

    def infer_scene_from_command(self, command: str, terminal_text: str):
        cmd = command.strip().lower()

        scene_map = {
            'mrkn wakeup ~ 1.': 'wakeup',
            'mrktxt photo ~ *remembered*.': 'photo',
            'reveal:photo.': 'photo',
            'mrktxt note ~ *unfolded*.': 'note',
            'reveal:note.': 'note',
            "mrksym framekey ~ 'k'.": 'framekey',
            "eyes:framekey ~~ 'k':mrkn drawer ~ 1.": 'drawer',
            'mrktxt letters ~ *unsealed*.': 'letters',
            'reveal:letters.': 'letters',
            'mrktxt truth ~ *veilgone*.': 'truth',
            'eyes:wakeup ~~ 1:mrktxt truth ~ *veilgone*.': 'truth',
            'eyes:wakeup ~~ 1:reveal:truth.': 'truth',
            'mrktxt grief ~ *witnessed*.': 'grief',
            'reveal:grief.': 'grief',
            'reveal:all.': 'all',
        }

        return scene_map.get(cmd)

    def advance_story(self):
        if self.story_stage < len(self.story_beats):
            key, line = self.story_beats[self.story_stage]
            self.story_stage += 1
            self._load_scene(key)
            self._append_story(line)
        else:
            self._append_story('The cabin has told you everything it can for now. The rest must be uncovered through the terminal.')
            self._load_scene('truth')

    def reset_memory(self):
        self.compiler.SYMBOL_TABLE.clear()
        self.compiler.CLASS_TABLE.clear()
        self.compiler.OBJECT_TABLE.clear()
        self.story_stage = 0
        self._load_scene('intro')
        self.story_text.configure(state='normal')
        self.story_text.delete('1.0', 'end')
        self.story_text.configure(state='disabled')
        self.terminal_output.configure(state='normal')
        self.terminal_output.delete('1.0', 'end')
        self.terminal_output.configure(state='disabled')
        self._show_intro_text()
        self._append_terminal('[SYSTEM] Memory cleared. The cabin starts over.')

    def submit_command(self):
        command = self.command_var.get().strip()
        if not command:
            return
        self.run_line(command)
        self.command_var.set('')

    def run_line(self, command: str):
        output_buffer = []

        def ui_story(line=''):
            output_buffer.append(line)

        original_story = self.compiler.story
        original_input = self.compiler.safe_user_input

        self.compiler.story = ui_story
        self.compiler.safe_user_input = lambda prompt, fallback='0': fallback

        try:
            self.compiler.compile_line(command)
        except Exception as exc:
            output_buffer.append(f'[UI ERROR] {exc}')
        finally:
            self.compiler.story = original_story
            self.compiler.safe_user_input = original_input

        self._append_terminal(f">>> {command}")
        terminal_text = '\n'.join(output_buffer).strip()
        if terminal_text:
            self._append_terminal(terminal_text)
        self._append_terminal('')

        scene_key = self.infer_scene_from_command(command, terminal_text)
        success = 'Status: COMPILATION SUCCESS' in terminal_text
        if scene_key and success:
            self._load_scene(scene_key)
        elif scene_key and not success:
            self._append_story('The command matched a story beat, but the compiler rejected it, so the scene did not advance.')

        story_lore_lines = [line for line in output_buffer if line.startswith('Story Lore:')]
        if story_lore_lines:
            self._append_story('\n'.join(story_lore_lines))
        elif scene_key and scene_key in self.scene_map:
            self._append_story(self.scene_map[scene_key]['text'])


if __name__ == '__main__':
    root = tk.Tk()
    app = StarRuneSondersUI(root)
    root.mainloop()
