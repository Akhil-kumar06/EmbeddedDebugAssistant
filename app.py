import pathlib,queue,threading,tkinter as tk
from tkinter import filedialog,messagebox,ttk
from tkinter.scrolledtext import ScrolledText
from core import analyze,format_report
from local_ai import ask
from runner import run_build
ROOT=pathlib.Path(__file__).resolve().parent
app=tk.Tk();app.title('Embedded Debug Assistant | Local AI');app.geometry('1120x820')
app.configure(bg='#101827');app.minsize(850,650)
status=tk.StringVar(value='Load a recorded log or try a synthetic example.')
question=tk.StringVar(value='What faults occurred, what evidence supports them, and what should I check next?')
report='';busy=False;messages=queue.Queue();controls=[]
tk.Label(app,text='EMBEDDED DEBUG ASSISTANT',font=('Arial',23,'bold'),fg='#67e8f9',bg='#101827').pack(anchor='w',padx=22,pady=(18,4))
tk.Label(app,text='FirmwareLab + CANLab | recorded evidence | local Ollama | v0.1',fg='#cbd5e1',bg='#101827').pack(anchor='w',padx=23)
bar=tk.Frame(app,bg='#101827');bar.pack(fill='x',padx=22,pady=12)
def replace(widget,text):
    widget.configure(state='normal');widget.delete('1.0','end');widget.insert('1.0',text);widget.configure(state='disabled')
def load(path=None):
    global report
    if busy:return
    path=path or filedialog.askopenfilename(filetypes=[('JSON lines','*.jsonl'),('All files','*.*')])
    if not path:return
    try:new_report=format_report(analyze(path))
    except Exception as e:messagebox.showerror('Cannot analyze',str(e));return
    report=new_report;replace(evidence,report);replace(response,'');status.set('Loaded: '+str(path))
def set_busy(value):
    global busy
    busy=value
    for b in controls:b.configure(state='disabled' if value else 'normal')
    ai_button.configure(state='disabled' if value else 'normal')
def work(fn,label):
    if busy:return
    set_busy(True);status.set(label)
    def task():
        try:messages.put(('ok',fn()))
        except Exception as e:messages.put(('error',str(e)))
    threading.Thread(target=task,daemon=True).start()
def explain():
    if not report:messagebox.showinfo('Load evidence','Load telemetry first.');return
    prompt=question.get().strip()
    if prompt:
        snapshot=report
        work(lambda:ask(snapshot,prompt),'Waiting for local AI; initial model load may take time...')
def build():
    folder=filedialog.askdirectory(title='Select trusted FirmwareLab or CANLab project')
    if not folder:return
    if not (pathlib.Path(folder)/'build.py').is_file():messagebox.showerror('Folder','Choose the folder containing build.py.');return
    if not messagebox.askyesno('Run project code?',f'Run python3 build.py in Ubuntu for:\n{folder}\n\nThis executes project code and writes build outputs. Select only your trusted project. Continue?'):return
    work(lambda:run_build(folder),'Running project build/tests in Ubuntu...')
for label,fn in [('Load telemetry',load),('CAN example',lambda:load(ROOT/'samples/can_example.jsonl')),
                 ('Firmware example',lambda:load(ROOT/'samples/firmware_example.jsonl')),('Run project build/tests',build)]:
    b=ttk.Button(bar,text=label,command=fn);b.pack(side='left',padx=(0,8));controls.append(b)
tk.Label(app,text='EVIDENCE — deterministic checks',fg='#67e8f9',bg='#101827').pack(anchor='w',padx=22)
evidence=ScrolledText(app,height=16,bg='#172338',fg='#e2e8f0',wrap='word',font=('Consolas',10))
evidence.pack(fill='both',expand=True,padx=22,pady=6);evidence.configure(state='disabled')
ttk.Entry(app,textvariable=question).pack(fill='x',padx=22,pady=5)
ai_button=ttk.Button(app,text='Explain evidence with local AI',command=explain);ai_button.pack(anchor='w',padx=22,pady=5)
tk.Label(app,text='AI EXPLANATION / TEST OUTPUT — verify suggestions against evidence',fg='#fbbf24',bg='#101827').pack(anchor='w',padx=22)
response=ScrolledText(app,height=12,bg='#172338',fg='#e2e8f0',wrap='word',font=('Consolas',10))
response.pack(fill='both',expand=True,padx=22,pady=6);response.configure(state='disabled')
tk.Label(app,textvariable=status,fg='#94a3b8',bg='#101827',anchor='w',wraplength=1060).pack(fill='x',padx=22,pady=(4,12))
def poll():
    try:
        kind,text=messages.get_nowait();replace(response,text);set_busy(False)
        status.set('Done. Verify AI explanations against the evidence.' if kind=='ok' else 'Action failed; details shown above.')
    except queue.Empty:pass
    app.after(100,poll)
def close():
    if busy:messagebox.showinfo('Action in progress','Wait for the action to complete or time out before closing.');return
    app.destroy()
app.protocol('WM_DELETE_WINDOW',close);app.after(100,poll);app.mainloop()
