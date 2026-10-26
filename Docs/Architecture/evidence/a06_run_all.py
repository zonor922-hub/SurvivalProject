"""Run with UnrealEditor-Cmd -ExecutePythonScript, not a commandlet; no asset saves."""
import json
import pathlib
import unreal

folder = pathlib.Path(__file__).resolve().parent
for name, result in (('a05_verify.py', 'a05_verification.json'), ('a06_verify.py', 'a06_verification.json')):
    script = folder / name
    output = folder / result
    original = output.read_bytes() if name == 'a05_verify.py' else None
    try:
        exec(compile(script.read_text(encoding='utf-8'), str(script), 'exec'), {'__file__': str(script)})
        if name == 'a05_verify.py':
            (folder / 'a06_a05_regression.json').write_bytes(output.read_bytes())
        assert json.loads(output.read_text(encoding='utf-8'))['passed'], result
    finally:
        if original is not None:
            output.write_bytes(original)

unreal.EditorPythonScripting.set_keep_python_script_alive(True)
try:
    script = folder / 'a06_pie.py'
    # Callback globals must survive until the three PIE sessions finish.
    globals()['_a6_headless'] = True
    globals()['__file__'] = str(script)
    exec(compile(script.read_text(encoding='utf-8'), str(script), 'exec'), globals())
except Exception:
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    raise
