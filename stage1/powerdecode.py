#!/usr/bin/env python3
"""Decode the Powershell command lines which were encoded in inject.bin"""
import base64
import codecs

# Common prefix
PREFIX = (
    'function write_file_bytes{' +
    'param([Byte[]] $file_bytes, [string] $file_path = ".\\stage2.zip");' +
    '$f = [io.file]::OpenWrite($file_path);' +
    '$f.Seek($f.Length,0);' +
    '$f.Write($file_bytes,0,$file_bytes.Length);' +
    '$f.Close();' +
    '}' +
    'function check_correct_environment{' +
    '$e=[Environment]::CurrentDirectory.split("\\");' +
    '$e=$e[$e.Length-1]+[Environment]::UserName;' +
    '$e -eq "challenge2015sstic";' +
    '}' +
    'if(check_correct_environment){' +
    'write_file_bytes([Convert]::FromBase64String(\'')
SUFFIX = (
    "'));" +
    "}else{" +
    "write_file_bytes([Convert]::FromBase64String('VAByAHkASABhAHIAZABlAHIA'));" +
    "}")

with open('decoded.out.txt', 'r') as fin:
    with open('stage2.zip', 'wb') as fout:
        for line in fin:
            if line.startswith('powershell -enc '):
                cmd = base64.b64decode(line[len('powershell -enc '):])
                cmd = codecs.decode(cmd, 'utf16')
                if cmd.startswith(PREFIX) and cmd.endswith(SUFFIX):
                    fout.write(base64.b64decode(cmd[len(PREFIX):-len(SUFFIX)]))
                else:
                    print(cmd)
