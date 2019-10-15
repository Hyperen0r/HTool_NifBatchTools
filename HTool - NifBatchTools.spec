# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['src\\HTool.py'],
             pathex=['venv/Lib/site-packages', 'D:\\Workspace\\PyQt\\HTool_NifBatchTools'],
             binaries=[],
             datas=[('venv/Lib/site-packages/pyffi/VERSION','pyffy')],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='HTool - NifBatchTools',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )
