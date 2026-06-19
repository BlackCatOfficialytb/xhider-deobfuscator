"""Patch psu_hard_mode/fibo.lua to dump the parsed proto as JSON.
Adapted from dump_payload.py for fibo.lua which uses g(Z(),{},U()).
"""
import subprocess
import pathlib
import os
import json

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / 'fibo.lua'
PATCHED = ROOT / 'fibo.dump.lua'
DUMP_PROTO = ROOT / 'fibo.proto.json'

LUA = os.environ.get('LUA', 'lua5.1')

LUA_FLAT_SER = r"""
local function flatser(root)
  local ids = {}
  local order = {}
  local function getid(v)
    if type(v) ~= 'table' then return nil end
    local id = ids[v]
    if id then return id end
    id = #order + 1
    ids[v] = id
    order[id] = v
    return id
  end
  getid(root)
  local function jstr(s)
    local r = {'"'}
    for i = 1, #s do
      local b = string.byte(s, i)
      if b == 34 then r[#r+1] = '\\"'
      elseif b == 92 then r[#r+1] = '\\\\'
      elseif b == 10 then r[#r+1] = '\\n'
      elseif b == 13 then r[#r+1] = '\\r'
      elseif b == 9 then r[#r+1] = '\\t'
      elseif b < 32 or b == 127 then r[#r+1] = string.format('\\u%04x', b)
      else r[#r+1] = string.char(b) end
    end
    r[#r+1] = '"'
    return table.concat(r)
  end
  local function jval(v)
    local tv = type(v)
    if tv == 'nil' then return 'null'
    elseif tv == 'boolean' then return tostring(v)
    elseif tv == 'number' then
      if v ~= v then return '"NaN"'
      elseif v == math.huge then return '"Inf"'
      elseif v == -math.huge then return '"-Inf"'
      elseif v == math.floor(v) and math.abs(v) < 1e15 then
        return string.format('%d', v)
      else
        return string.format('%.17g', v)
      end
    elseif tv == 'string' then return jstr(v)
    elseif tv == 'table' then return string.format('{"$ref":%d}', getid(v))
    else return string.format('"<%s>"', tv) end
  end
  local out = {'{"root":1,"nodes":{'}
  local i = 1
  while i <= #order do
    local node = order[i]
    if i > 1 then out[#out+1] = ',' end
    out[#out+1] = string.format('"%d":{', i)
    local first = true
    for k, v in pairs(node) do
      if not first then out[#out+1] = ',' end
      first = false
      out[#out+1] = jstr(tostring(k))
      out[#out+1] = ':'
      out[#out+1] = jval(v)
    end
    out[#out+1] = '}'
    i = i + 1
    for _, v in pairs(node) do
      if type(v) == 'table' then getid(v) end
    end
  end
  out[#out+1] = '}}'
  return table.concat(out)
end
"""


def patch_source(s: str) -> str:
    propath = str(DUMP_PROTO).replace('\\', '/')

    # fibo.lua uses: return g(Z(),{},U())(...);end)(({...});
    # Z() = LZW decompressor returning proto table
    # U() = getfenv wrapper
    # g() = VM executor
    needle = 'return g(Z(),{},U())(...);end)(({'

    flatser_inline = LUA_FLAT_SER.replace('\n', ' ')
    repl = (
        'do local _proto=Z() '
        + flatser_inline + ' '
        'local data = flatser(_proto) '
        'local _f2=io.open([[' + propath + ']],[[w]]) '
        '_f2:write(data) _f2:close() '
        'os.exit(0) end '
        'return g(Z(),{},U())(...);end)(({'
    )
    s = s.replace(needle, repl, 1)
    assert 'flatser' in s, 'replacement failed'
    return s


def main():
    src = SRC.read_text(encoding='utf-8')
    patched = patch_source(src)
    PATCHED.write_text(patched, encoding='utf-8')
    print(f'patched -> {PATCHED} (len={len(patched)})')
    if DUMP_PROTO.exists():
        DUMP_PROTO.unlink()
    try:
        cmd = [LUA, str(PATCHED)]
        print(f'Running: {" ".join(cmd)}')
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        print('rc:', r.returncode)
        if r.stdout:
            print('stdout:', r.stdout[:2000])
        if r.stderr:
            print('stderr:', r.stderr[:2000])
    except subprocess.TimeoutExpired:
        print('TIMEOUT')
    print()
    if DUMP_PROTO.exists():
        print(f'  {DUMP_PROTO.name}: {DUMP_PROTO.stat().st_size} bytes')
    else:
        print(f'  {DUMP_PROTO.name}: MISSING')


if __name__ == '__main__':
    main()