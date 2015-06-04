#!/usr/bin/env python3
"""Decode an ST20 firmware containing code and data"""

def to_signed32(value):
    """Make an unsigned 32-bit number signed in Python"""
    if value & 0x80000000:
        return -((-value) & 0xffffffff)
    return value & 0xffffffff


def to_decorhex(value):
    """Represent a number in decimal or hexadecimal depending on its value"""
    return str(value) if 0 <= value < 16 else hex(to_signed32(value))


class PushExpr(object):
    """Represent an expression which is pushed on the stack with maybe several
    instructions.

    If the value is an integer, it is a constant which can be combined with
    other push instructions.
    Otherwise, the value is a string describing the expression which is
    computed in pseudo-code.
    """
    def __init__(self, filemeta, iaddr, isize, value, previous=None):
        """Define a new pushed expression in the given FileMeta object.

        previous is another PushExpr object which was previosly pushed
        """
        self.filemeta = filemeta
        self.iaddr = iaddr
        self.isize = isize
        self.value = value
        self.previous = previous
        self.addparens = False  # Add parentheses around the value

    def __str__(self):
        if self.addparens:
            return '(' + self.value + ')'
        elif not isinstance(self.value, int):
            # the value is already a string
            return self.value
        elif 0 <= self.value < 16:
            return str(self.value)
        return hex(self.value)

    def show(self):
        """Show the pushed value as a pseudo-code instruction"""
        if self.previous:
            self.previous.show()
        desc = 'Push ' + str(self)
        self.filemeta.show_instruction(self.iaddr, self.isize, desc)

    def add(self, isize, value):
        """Merge an instruction of size isize which adds the given value to the
        top of the stack"""
        self.isize += isize
        if isinstance(self.value, int):
            self.value = (self.value + value) & 0xffffffff
        else:
            self.value = '({})+{}'.format(self.value, value)

    def merge1(self, isize, opformat, addparens=True):
        """Merge an instruction which operates on the stack top"""
        self.isize += isize
        self.value = opformat.format(str(self))
        self.addparens = addparens

    def merge2(self, isize, opformat, addparens=True):
        """Merge an instruction of size isize which has 2 operands"""
        if self.previous is None:
            self.isize += isize
            self.value = opformat.format(A=str(self), B='Pop')
            self.addparens = addparens
        else:
            self.value = opformat.format(A=str(self), B=str(self.previous))
            self.iaddr = self.previous.iaddr
            self.isize += self.previous.isize + isize
            self.previous = self.previous.previous
            self.addparens = addparens


class FileMeta(object):
    """Store the specific meta-information which help decoding the file.

    This information consists in code labels, data labels and comments
    """
    def __init__(self, mem, first_addr, codelab, datalab, comments):
        """
        Initialize a file which content is in mem, loaded at address
        first_addr in virtual memory, with the given meta-information
        """
        self.mem = mem
        self.first_addr = first_addr
        self.codelab = codelab
        self.datalab = datalab
        self.comments = comments

    def show_instruction(self, iaddr, isize, desc=None):
        """Show instruction at virtual address iaddr, size isize

        desc is an additional description. "None" means displaying the ASCII
        representation of the bytes, if available
        """
        ioffset = iaddr - self.first_addr
        assert 0 <= ioffset < ioffset + isize <= len(self.mem)
        idata = self.mem[ioffset:ioffset + isize]

        if desc is None:
            # Show ASCII characters like an hexadecimal dump
            desc = ''.join(chr(b) if 32 <= b < 127 else '\\x{:02x}'.format(b) for b in idata)
            desc = '"{}"'.format(desc)
        if isize > 8:
            # Show description on the next line if it is too long
            desc = '\n                                 ' + desc

        comment = self.comments.get(iaddr, '')
        if comment:
            comment = ' # ' + comment
        line = '  {:04x}: '.format(iaddr)
        while len(idata):
            line += '{:25s}'.format(' '.join('{:02x}'.format(b) for b in idata[:16]))
            idata = idata[16:]
            if len(idata):
                line += '\n        '
        print(line + desc + comment)

    def show_all(self):
        """Show all instructions in the file"""
        in_code = False
        cur_offset = 0  # Offset in self.mem
        cur_pushexpr = None  # Combine constants together using PushExpr

        while cur_offset < len(self.mem):
            iaddr = self.first_addr + cur_offset

            # Label management, to jump into code or data
            label = self.codelab.get(iaddr)
            if label is not None:
                in_code = True
            else:
                label = self.datalab.get(iaddr)
                if label is not None:
                    in_code = False
            if label is not None:
                if cur_pushexpr is not None:
                    cur_pushexpr.show()
                    cur_pushexpr = None
                print("\n{}:".format(label))

            isize = 1
            if in_code:
                # Decode instruction
                desc = 'Unknown instruction'
                instr = self.mem[cur_offset]
                icode = instr & 0xf0
                oreg = instr & 0x0f

                # Read prefix
                while icode in (0x20, 0x60) and cur_offset + isize < len(self.mem):
                    if icode == 0x20:  # PFIX, Prefix
                        oreg = (oreg << 4) & 0xffffffff
                    else:
                        assert icode == 0x60  # NFIX, Negative Prefix
                        oreg = ((~oreg) << 4) & 0xffffffff
                    icode = self.mem[cur_offset + isize] & 0xf0
                    oreg |= self.mem[cur_offset + isize] & 0x0f
                    isize += 1

                # Decode instruction
                if icode == 0x00:  # J, Jump
                    destaddr = iaddr + isize + to_signed32(oreg)
                    label = self.codelab.get(destaddr, '??')
                    desc = 'Jump {:#04x} <{}>'.format(destaddr, label)

                elif icode == 0x10:  # LDLP, Load Local Pointer
                    expr = 'ptr W[{}]'.format(to_decorhex(oreg))
                    cur_pushexpr = PushExpr(self, iaddr, isize, expr, cur_pushexpr)
                    cur_offset += isize
                    continue

                elif icode == 0x30:  # LDNL, Load Non-Local
                    if cur_pushexpr is None:
                        desc = 'A = A[{:#x}]'.format(to_signed32(oreg))
                    else:
                        cur_pushexpr = PushExpr(
                            self,
                            cur_pushexpr.iaddr,
                            cur_pushexpr.isize + isize,
                            '({})[{:#x}]'.format(str(cur_pushexpr), to_signed32(oreg)))
                        cur_offset += isize
                        continue

                elif icode == 0x40:  # LDC, Load Constant
                    cur_pushexpr = PushExpr(self, iaddr, isize, oreg, cur_pushexpr)
                    cur_offset += isize
                    continue

                elif icode == 0x50:  # LDNLP, Load Non-Local Pointer
                    if cur_pushexpr is None:
                        desc = 'A = ptr A[{:#x}]'.format(to_signed32(oreg))
                    else:  # Merge with a previous push
                        cur_pushexpr.add(isize, 4 * to_signed32(oreg))
                        cur_offset += isize
                        continue

                elif icode == 0x70:  # LDL, Load Local
                    expr = 'W[{}]'.format(to_decorhex(oreg))
                    cur_pushexpr = PushExpr(self, iaddr, isize, expr, cur_pushexpr)
                    cur_offset += isize
                    continue

                elif icode == 0x80:  # ADC, Add Constant
                    if cur_pushexpr is None:
                        desc = 'A += {:#x}'.format(to_signed32(oreg))
                    else:
                        cur_pushexpr.add(isize, to_signed32(oreg))
                        cur_offset += isize
                        continue

                elif icode == 0x90:  # CALL, Subroutine Call
                    destaddr = iaddr + isize + to_signed32(oreg)
                    label = self.codelab.get(destaddr, '??')
                    desc = 'Call {:#04x} <{}>'.format(destaddr, label)

                elif icode == 0xa0:  # CJ, Conditional Jump
                    destaddr = iaddr + isize + to_signed32(oreg)
                    label = self.codelab.get(destaddr, '??')
                    desc = 'If A=0 Jump {:#04x} <{}> else Pop'.format(destaddr, label)

                elif icode == 0xb0:  # AJW, Adjust Workspace
                    desc = 'W += 4 * {:#x}'.format(to_signed32(oreg))

                elif icode == 0xc0:  # EQC, Equals Constant
                    desc = 'A = (A == {:#x}) ? 1 : 0'.format(oreg)

                elif icode == 0xd0:  # STL, Store Local
                    soreg = to_signed32(oreg)
                    if cur_pushexpr is None:
                        desc = 'W[{}] = Pop'.format(to_decorhex(oreg))
                    else:
                        desc = 'W[{}] = {}'.format(to_decorhex(oreg), str(cur_pushexpr))
                        cur_offset -= cur_pushexpr.isize
                        isize += cur_pushexpr.isize
                        cur_pushexpr = cur_pushexpr.previous

                elif icode == 0xe0:  # STNL, Store Non-Local
                    desc = 'A[{:#x}] = B, Pop, Pop'.format(to_signed32(oreg))

                elif icode == 0xf0:  # OPR, Operate (extended instruction set)
                    desc = '\033[31;1mUnknown OPR {:#x}\033[m'.format(oreg)

                    if oreg == 0x01:  # LB, Load Byte
                        if cur_pushexpr is None:
                            desc = 'A = loadbyte(A)'
                        else:
                            cur_pushexpr.addparens = False
                            cur_pushexpr.merge1(isize, 'LB({})', False)
                            cur_offset += isize
                            continue

                    elif oreg == 0x02:  # BSUB, Byte Subscript
                        if cur_pushexpr is None:
                            desc = 'BSUB (A += B, pop)'
                        else:
                            cur_pushexpr.merge2(isize, '{A}+{B}')
                            cur_offset += isize
                            continue

                    elif oreg == 0x06:  # GCALL, General Call
                        desc = 'GCALL (swap A, IPtr)'

                    elif oreg == 0x07:  # IN(address=C, channel=B, length=A)
                        lendesc = 'A'
                        chandesc = 'B'
                        addrdesc = 'C'
                        if cur_pushexpr is not None:
                            lendesc = str(cur_pushexpr)
                            cur_offset -= cur_pushexpr.isize
                            isize += cur_pushexpr.isize
                            cur_pushexpr = cur_pushexpr.previous
                        if cur_pushexpr is not None:
                            chandesc = str(cur_pushexpr)
                            cur_offset -= cur_pushexpr.isize
                            isize += cur_pushexpr.isize
                            cur_pushexpr = cur_pushexpr.previous
                        if cur_pushexpr is not None:
                            addrdesc = str(cur_pushexpr)
                            cur_offset -= cur_pushexpr.isize
                            isize += cur_pushexpr.isize
                            cur_pushexpr = cur_pushexpr.previous
                        desc = 'IN(addr={}, chan={}, len={})'.format(
                            addrdesc, chandesc, lendesc)

                    elif oreg == 0x08:  # PROD, Product
                        if cur_pushexpr is None:
                            desc = 'PROD (1 *= B, pop)'
                        else:
                            cur_pushexpr.merge2(isize, '{A}*{B}')
                            cur_offset += isize
                            continue

                    elif oreg == 0x09:  # GT, Greater Than
                        if cur_pushexpr is None:
                            desc = 'GT (A = (B > A ? 1 : 0), pop)'
                        else:
                            cur_pushexpr.merge2(isize, '({B} > {A}) ? 1 : 0')
                            cur_offset += isize
                            continue

                    elif oreg == 0x0a:  # WSUB, Word Subscript
                        if cur_pushexpr is None:
                            desc = 'WSUB (A += 4*B, pop)'
                        else:
                            cur_pushexpr.merge2(isize, '{A}+4*{B}')
                            cur_offset += isize
                            continue

                    elif oreg == 0x0b:  # OUT(address=C, channel=B, length=A)
                        lendesc = 'A'
                        chandesc = 'B'
                        addrdesc = 'C'
                        if cur_pushexpr is not None:
                            lendesc = str(cur_pushexpr)
                            cur_offset -= cur_pushexpr.isize
                            isize += cur_pushexpr.isize
                            cur_pushexpr = cur_pushexpr.previous
                        if cur_pushexpr is not None:
                            chandesc = str(cur_pushexpr)
                            cur_offset -= cur_pushexpr.isize
                            isize += cur_pushexpr.isize
                            cur_pushexpr = cur_pushexpr.previous
                        if cur_pushexpr is not None:
                            addrdesc = str(cur_pushexpr)
                            addrval = cur_pushexpr.value
                            if isinstance(addrval, int) and addrval in self.datalab:
                                addrdesc += ' <{}>'.format(self.datalab[addrval])
                            cur_offset -= cur_pushexpr.isize
                            isize += cur_pushexpr.isize
                            cur_pushexpr = cur_pushexpr.previous
                        desc = 'OUT(addr={}, chan={}, len={})'.format(
                            addrdesc, chandesc, lendesc)

                    elif oreg == 0x1b:  # LDPI, Load Pointer to Instruction
                        if cur_pushexpr is None:
                            desc = 'A += {:#x}'.format(iaddr + isize)
                        else:
                            cur_pushexpr.add(isize, iaddr + isize)
                            cur_offset += isize
                            continue

                    elif oreg == 0x1f:  # REM, Remainder
                        if cur_pushexpr is None:
                            desc = 'REM (A = B % A, pop)'
                        else:
                            cur_pushexpr.merge2(isize, '{B}%{A}')
                            cur_offset += isize
                            continue

                    elif oreg == 0x20:  # RET, Return from a function call
                        desc = 'Return'

                    elif oreg == 0x33:  # XOR
                        if cur_pushexpr is None:
                            desc = 'XOR (A = B ^ A, pop)'
                        else:
                            cur_pushexpr.merge2(isize, '{B} ^ {A}')
                            cur_offset += isize
                            continue

                    elif oreg == 0x3b:  # SB, Store Byte
                        if cur_pushexpr is None:
                            desc = 'storebyte(A, B), pop2'
                        else:
                            cur_pushexpr.merge2(0, 'SB:{A} = {B}')
                            desc = cur_pushexpr.value
                            cur_offset -= cur_pushexpr.isize
                            isize += cur_pushexpr.isize
                            cur_pushexpr = cur_pushexpr.previous

                    elif oreg == 0x3c:  # GAJW, General Adjust Workspace, swap A and W
                        if cur_pushexpr is None:
                            desc = 'SWAP(A, W)'
                        else:
                            desc = 'Push W; W = {}'.format(str(cur_pushexpr))
                            cur_offset -= cur_pushexpr.isize
                            isize += cur_pushexpr.isize
                            cur_pushexpr = cur_pushexpr.previous

                    elif oreg == 0x40:  # SHR, Shift Right
                        if cur_pushexpr is None:
                            desc = 'SHR (A = B >> A, pop)'
                        else:
                            cur_pushexpr.merge2(isize, '{B}>>{A}')
                            cur_offset += isize
                            continue

                    elif oreg == 0x41:  # SHL, Shift Left
                        if cur_pushexpr is None:
                            desc = 'SHL (A = B << A, pop)'
                        else:
                            cur_pushexpr.merge2(isize, '{B}<<{A}')
                            cur_offset += isize
                            continue

                    elif oreg == 0x42:  # MINT, push 0x80000000
                        cur_pushexpr = PushExpr(self, iaddr, isize, 0x80000000, cur_pushexpr)
                        cur_offset += isize
                        continue

                    elif oreg == 0x46:  # AND
                        if cur_pushexpr is None:
                            desc = 'AND (A = B & A, pop)'
                        else:
                            cur_pushexpr.merge2(isize, '{B}&{A}')
                            cur_offset += isize
                            continue

                    elif oreg == 0x5a:  # DUP
                        desc = 'DUP (Push A)'

                    elif oreg == 0xc1:  # SSUB, 16-bit word subscript
                        if cur_pushexpr is None:
                            desc = 'SSUB (A += 2*B, pop)'
                        else:
                            cur_pushexpr.merge2(isize, '{A}+2*{B}')
                            cur_offset += isize
                            continue
            else:
                # Show data
                desc = None
                while isize < 16 and cur_offset + isize < len(self.mem):
                    if iaddr + isize in self.codelab:
                        break
                    if iaddr + isize in self.datalab:
                        break
                    isize += 1

            # Show all previous push instructions
            if cur_pushexpr is not None:
                cur_pushexpr.show()
                cur_pushexpr = None
            # Show current instruction and go to the next one
            self.show_instruction(self.first_addr + cur_offset, isize, desc)
            cur_offset += isize
