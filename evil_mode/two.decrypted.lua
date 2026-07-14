-- XHider evil_mode Deobfuscated
-- Method: string constant decryption + inner payload extraction
-- Original: two.lua (108KB anti-tamper framework)
-- Anti-tamper: pcall validation, error line number checks, _G metatable locks,
--              debug.gethook checks, 100+ integrity iterations
-- Inner payload: self-contained XOR-decrypted print("helloworld")

-- Reconstructed source (bypassing anti-tamper):
print("helloworld")
