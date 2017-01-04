# Copyright (C) Microsoft Corporation. All rights reserved.
# Licensed under the MIT license. See COPYRIGHT in the project root for full license information.
import argparse
from hctdb import *

# get db singletons
g_db_dxil = None
def get_db_dxil():
    global g_db_dxil
    if g_db_dxil is None:
        g_db_dxil = db_dxil()
    return g_db_dxil
g_db_hlsl = None
def get_db_hlsl():
    global g_db_hlsl
    if g_db_hlsl is None:
        g_db_hlsl = db_hlsl()
    return g_db_hlsl

def format_comment(prefix, val):
    "Formats a value with a line-comment prefix."
    result = ""
    line_width = 80
    content_width = line_width - len(prefix)
    l = len(val)
    while l:
        if l < content_width:
            result += prefix + val.strip()
            result += "\n"
            l = 0
        else:
            split_idx = val.rfind(" ", 0, content_width)
            result += prefix + val[:split_idx].strip()
            result += "\n"
            val = val[split_idx+1:]
            l = len(val)
    return result

def format_rst_table(list_of_tuples):
    "Produces a reStructuredText simple table from the specified list of tuples."
    # Calculate widths.
    widths = None
    for t in list_of_tuples:
        if widths is None:
            widths = [0] * len(t)
        for i, v in enumerate(t):
            widths[i] = max(widths[i], len(str(v)))
    # Build banner line.
    banner = ""
    for i, w in enumerate(widths):
        if i > 0:
            banner += " "
        banner += "=" * w
    banner += "\n"
    # Build the result.
    result = banner
    for i, t in enumerate(list_of_tuples):
        for j, v in enumerate(t):
            if j > 0:
                result += " "
            result += str(v)
            result += " " * (widths[j] - len(str(v)))
        result = result.rstrip()
        result += "\n"
        if i == 0:
            result += banner
    result += banner
    return result

def build_range_tuples(i):
    "Produces a list of tuples with contiguous ranges in the input list."
    i = sorted(i)
    low_bound = None
    high_bound = None
    for val in i:
        if low_bound is None:
            low_bound = val
            high_bound = val
        else:
            assert(not high_bound is None)
            if val == high_bound + 1:
                high_bound = val
            else:
                yield (low_bound, high_bound)
                low_bound = val
                high_bound = val
    if not low_bound is None:
        yield (low_bound, high_bound)

def build_range_code(var, i):
    "Produces a fragment of code that tests whether the variable name matches values in the given range."
    ranges = build_range_tuples(i)
    result = ""
    for r in ranges:
        if r[0] == r[1]:
            cond = var + " == " + str(r[0])
        else:
            cond = "%d <= %s && %s <= %d" % (r[0], var, var, r[1])
        if result == "":
            result = cond
        else:
            result = result + " || " + cond
    return result

class db_docsref_gen:
    "A generator of reference documentation."
    def __init__(self, db):
        self.db = db
        instrs = [i for i in self.db.instr if i.is_dxil_op]
        instrs = sorted(instrs, key=lambda v : ("" if v.category == None else v.category) + "." + v.name)
        self.instrs = instrs
        val_rules = sorted(db.val_rules, key=lambda v : ("" if v.category == None else v.category) + "." + v.name)
        self.val_rules = val_rules

    def print_content(self):
        self.print_header()
        self.print_body()
        self.print_footer()

    def print_header(self):
        print("<!DOCTYPE html>")
        print("<html><head><title>DXIL Reference</title>")
        print("<style>body { font-family: Verdana; font-size: small; }</style>")
        print("</head><body><h1>DXIL Reference</h1>")
        self.print_toc("Instructions", "i", self.instrs)
        self.print_toc("Rules", "r", self.val_rules)

    def print_body(self):
        self.print_instruction_details()
        self.print_valrule_details()

    def print_instruction_details(self):
        print("<h2>Instruction Details</h2>")
        for i in self.instrs:
            print("<h3><a name='i%s'>%s</a></h3>" % (i.name, i.name))
            print("<div>Opcode: %d. This instruction %s.</div>" % (i.dxil_opid, i.doc))
            if i.remarks:
                # This is likely a .rst fragment, but this will do for now.
                print("<div> " + i.remarks + "</div>")
            print("<div>Operands:</div>")
            print("<ul>")
            for o in i.ops:
                if o.pos == 0:
                    print("<li>result: %s - %s</li>" % (o.llvm_type, o.doc))
                else:
                    enum_desc = "" if o.enum_name == "" else " one of %s: %s" % (o.enum_name, ",".join(db.enum_idx[o.enum_name].value_names()))
                    print("<li>%d - %s: %s%s%s</li>" % (o.pos - 1, o.name, o.llvm_type, "" if o.doc == "" else " - " + o.doc, enum_desc))
            print("</ul>")
            print("<div><a href='#Instructions'>(top)</a></div>")

    def print_valrule_details(self):
        print("<h2>Rule Details</h2>")
        for i in self.val_rules:
            print("<h3><a name='r%s'>%s</a></h3>" % (i.name, i.name))
            print("<div>" + i.doc + "</div>")
            print("<div><a href='#Rules'>(top)</a></div>")

    def print_toc(self, name, aprefix, values):
        print("<h2><a name='" + name + "'>" + name + "</a></h2>")
        last_category = ""
        for i in values:
            if i.category != last_category:
                if last_category != None:
                    print("</ul>")
                print("<div><b>%s</b></div><ul>" % i.category)
                last_category = i.category
            print("<li><a href='#" + aprefix + "%s'>%s</a></li>" % (i.name, i.name))
        print("</ul>")

    def print_footer(self):
        print("</body></html>")


class db_instrhelp_gen:
    "A generator of instruction helper classes."
    def __init__(self, db):
        self.db = db
        self.llvm_type_map = {
            "i1": "bool",
            "i8": "int8_t",
            "u8": "uint8_t",
            "i32": "int32_t",
            "u32": "uint32_t"
            }

    def print_content(self):
        self.print_header()
        self.print_body()
        self.print_footer()

    def print_header(self):
        print("///////////////////////////////////////////////////////////////////////////////")
        print("//                                                                           //")
        print("// Copyright (C) Microsoft Corporation. All rights reserved.                 //")
        print("// DxilInstructions.h                                                        //")
        print("//                                                                           //")
        print("// This file provides a library of instruction helper classes.               //")
        print("//                                                                           //")
        print("// MUCH WORK YET TO BE DONE - EXPECT THIS WILL CHANGE - GENERATED FILE       //")
        print("//                                                                           //")
        print("///////////////////////////////////////////////////////////////////////////////")
        print("")
        print("// TODO: add correct include directives")
        print("// TODO: add accessors with values")
        print("// TODO: add validation support code, including calling into right fn")
        print("// TODO: add type hierarchy")
        print("namespace hlsl {")

    def bool_lit(self, val):
        return "true" if val else "false";

    def op_type(self, o):
        if o.llvm_type in self.llvm_type_map:
            return self.llvm_type_map[o.llvm_type]
        raise ValueError("Don't know how to describe type %s for operand %s." % (o.llvm_type, o.name))

    def op_const_expr(self, o):
        if o.llvm_type in self.llvm_type_map:
            return "(%s)(llvm::dyn_cast<llvm::ConstantInt>(Instr->getOperand(%d))->getZExtValue())" % (self.op_type(o), o.pos - 1)
        raise ValueError("Don't know how to describe type %s for operand %s." % (o.llvm_type, o.name))

    def print_body(self):
        for i in self.db.instr:
            if i.is_reserved: continue
            if i.inst_helper_prefix:
                struct_name = "%s_%s" % (i.inst_helper_prefix, i.name)
            elif i.is_dxil_op:
                struct_name = "DxilInst_%s" % i.name
            else:
                struct_name = "LlvmInst_%s" % i.name
            if i.doc:
                print("/// This instruction %s" % i.doc)
            print("struct %s {" % struct_name)
            print("  const llvm::Instruction *Instr;")
            print("  // Construction and identification")
            print("  %s(llvm::Instruction *pInstr) : Instr(pInstr) {}" % struct_name)
            print("  operator bool() const {")
            if i.is_dxil_op:
                op_name = i.fully_qualified_name()
                print("    return hlsl::OP::IsDxilOpFuncCallInst(Instr, %s);" % op_name)
            else:
                print("    return Instr->getOpcode() == llvm::Instruction::%s;" % i.name)
            print("  }")
            print("  // Validation support")
            print("  bool isAllowed() const { return %s; }" % self.bool_lit(i.is_allowed))
            if i.is_dxil_op:
                print("  bool isArgumentListValid() const {")
                print("    if (%d != llvm::dyn_cast<llvm::CallInst>(Instr)->getNumArgOperands()) return false;" % (len(i.ops) - 1))
                print("    return true;")
                # TODO - check operand types
                print("  }")
                AccessorsWritten = False
                for o in i.ops:
                    if o.pos > 1: # 0 is return type, 1 is
                        if not AccessorsWritten:
                            print("  // Accessors")
                            AccessorsWritten = True
                        print("  llvm::Value *get_%s() const { return Instr->getOperand(%d); }" % (o.name, o.pos - 1))
                        if o.is_const:
                            print("  %s get_%s_val() const { return %s; }" % (self.op_type(o), o.name, self.op_const_expr(o)))
            print("};")
            print("")

    def print_footer(self):
        print("} // namespace hlsl")

class db_enumhelp_gen:
    "A generator of enumeration declarations."
    def __init__(self, db):
        self.db = db
        # Some enums should get a last enum marker.
        self.lastEnumNames = {
            "OpCode": "NumOpCodes",
            "OpCodeClass": "NumOpClasses"
        }
    
    def print_enum(self, e, **kwargs):
        print("// %s" % e.doc)
        print("enum class %s : unsigned {" % e.name)
        hide_val = kwargs.get("hide_val", False)
        sorted_values = e.values
        if kwargs.get("sort_val", True):
            sorted_values = sorted(e.values, key=lambda v : ("" if v.category == None else v.category) + "." + v.name)
        last_category = None
        for v in sorted_values:
            if v.category != last_category:
                if last_category != None:
                    print("")
                print("  // %s" % v.category)
                last_category = v.category

            line_format = "  {name}"
            if not e.is_internal and not hide_val:
                line_format += " = {value}"
            line_format += ","
            if v.doc:
                line_format += " // {doc}"
            print(line_format.format(name=v.name, value=v.value, doc=v.doc))
        if e.name in self.lastEnumNames:
            print("")
            print("  " + self.lastEnumNames[e.name] + " = " + str(len(sorted_values)) + " // exclusive last value of enumeration")
        print("};")

    def print_content(self):
        for e in sorted(self.db.enums, key=lambda e : e.name):
            self.print_enum(e)

class db_oload_gen:
    "A generator of overload tables."
    def __init__(self, db):
        self.db = db
        instrs = [i for i in self.db.instr if i.is_dxil_op]
        self.instrs = sorted(instrs, key=lambda i : i.dxil_opid)

    def print_content(self):
        self.print_opfunc_props()
        print("...")
        self.print_opfunc_table()

    def print_opfunc_props(self):
        print("const OP::OpCodeProperty OP::m_OpCodeProps[(unsigned)OP::OpCode::NumOpCodes] = {")
        print("//   OpCode                       OpCode name,                OpCodeClass                    OpCodeClass name,              void,     h,     f,     d,    i1,    i8,   i16,   i32,   i64  function attribute")
        # Example formatted string:
        #   {  OC::TempRegLoad,             "TempRegLoad",              OCC::TempRegLoad,              "tempRegLoad",                false,  true,  true, false,  true, false,  true,  true, false, Attribute::ReadOnly, },
        # 012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789
        # 0         1         2         3         4         5         6         7         8         9         0         1         2         3         4         5         6         7         8         9         0

        last_category = None
        # overload types are a string of (v)oid, (h)alf, (f)loat, (d)ouble, (1)-bit, (8)-bit, (w)ord, (i)nt, (l)ong
        f = lambda i,c : "true," if i.oload_types.find(c) >= 0 else "false,"
        lower_exceptions = { "CBufferLoad" : "cbufferLoad", "CBufferLoadLegacy" : "cbufferLoadLegacy", "GSInstanceID" : "gsInstanceID" }
        lower_fn = lambda t: lower_exceptions[t] if t in lower_exceptions else t[:1].lower() + t[1:]
        attr_dict = { "": "None", "ro": "ReadOnly", "rn": "ReadNone" }
        attr_fn = lambda i : "Attribute::" + attr_dict[i.fn_attr] + ","
        for i in self.instrs:
            if last_category != i.category:
                if last_category != None:
                    print("")
                print("  // {category:118} void,     h,     f,     d,    i1,    i8,   i16,   i32,   i64  function attribute".format(category=i.category))
                last_category = i.category
            print("  {{  OC::{name:24} {quotName:27} OCC::{className:25} {classNameQuot:28} {v:>7}{h:>7}{f:>7}{d:>7}{b:>7}{e:>7}{w:>7}{i:>7}{l:>7} {attr:20} }},".format(
                name=i.name+",", quotName='"'+i.name+'",', className=i.dxil_class+",", classNameQuot='"'+lower_fn(i.dxil_class)+'",',
                v=f(i,"v"), h=f(i,"h"), f=f(i,"f"), d=f(i,"d"), b=f(i,"1"), e=f(i,"8"), w=f(i,"w"), i=f(i,"i"), l=f(i,"l"), attr=attr_fn(i)))
        print("};")
    
    def print_opfunc_table(self):
        # Print the table for OP::GetOpFunc
        op_type_texts = {
            "$cb": "CBRT(pETy);",
            "$o": "A(pETy);",
            "$r": "RRT(pETy);",
            "d": "A(pF64);",
            "dims": "A(pDim);",
            "f": "A(pF32);",
            "h": "A(pF16);",
            "i1": "A(pI1);",
            "i16": "A(pI16);",
            "i32": "A(pI32);",
            "i32c": "A(pI32C);",
            "i64": "A(pI64);",
            "i8": "A(pI8);",
            "$u4": "A(pI4S);",
            "pf32": "A(pPF32);",
            "res": "A(pRes);",
            "splitdouble": "A(pSDT);",
            "twoi32": "A(p2I32);",
            "twof32": "A(p2F32);",
            "fouri32": "A(p4I32);",
            "fourf32": "A(p4F32);",
            "u32": "A(pI32);",
            "u64": "A(pI64);",
            "u8": "A(pI8);",
            "v": "A(pV);",
            "w": "A(pWav);",
            "SamplePos": "A(pPos);",
        }
        last_category = None
        for i in self.instrs:
            if last_category != i.category:
                if last_category != None:
                    print("")
                print("    // %s" % i.category)
                last_category = i.category
            line = "  case OpCode::{name:24}".format(name = i.name + ":")
            for index, o in enumerate(i.ops):
                assert o.llvm_type in op_type_texts, "llvm type %s in instruction %s is unknown" % (o.llvm_type, i.name)
                op_type_text = op_type_texts[o.llvm_type]
                if index == 0:
                    line = line + "{val:13}".format(val=op_type_text)
                else:
                    line = line + "{val:9}".format(val=op_type_text)
            line = line + "break;"
            print(line)
    

class db_valfns_gen:
    "A generator of validation functions."
    def __init__(self, db):
        self.db = db

    def print_content(self):
        self.print_header()
        self.print_body()

    def print_header(self):
        print("///////////////////////////////////////////////////////////////////////////////")
        print("// Instruction validation functions.                                         //")

    def bool_lit(self, val):
        return "true" if val else "false";

    def op_type(self, o):
        if o.llvm_type == "i8":
            return "int8_t"
        if o.llvm_type == "u8":
            return "uint8_t"
        raise ValueError("Don't know how to describe type %s for operand %s." % (o.llvm_type, o.name))

    def op_const_expr(self, o):
        if o.llvm_type == "i8" or o.llvm_type == "u8":
            return "(%s)(llvm::dyn_cast<llvm::ConstantInt>(Instr->getOperand(%d))->getZExtValue())" % (self.op_type(o), o.pos - 1)
        raise ValueError("Don't know how to describe type %s for operand %s." % (o.llvm_type, o.name))

    def print_body(self):
        llvm_instrs = [i for i in self.db.instr if i.is_allowed and not i.is_dxil_op]
        print("static bool IsLLVMInstructionAllowed(llvm::Instruction &I) {")
        self.print_comment("  // ", "Allow: %s" % ", ".join([i.name + "=" + str(i.llvm_id) for i in llvm_instrs]))
        print("  unsigned op = I.getOpcode();")
        print("  return %s;" % build_range_code("op", [i.llvm_id for i in llvm_instrs]))
        print("}")
        print("")

    def print_comment(self, prefix, val):
        print(format_comment(prefix, val))

class macro_table_gen:
    "A generator for macro tables."

    def format_row(self, row, widths, sep=', '):
        frow = [str(item) + sep + (' ' * (width - len(item)))
                for item, width in zip(row, widths)[:-1]] + [str(row[-1])]
        return ''.join(frow)

    def format_table(self, table, *args, **kwargs):
        widths = [  reduce(max, [   len(row[i])
                                    for row in table], 1)
                    for i in range(len(table[0]))]
        formatted = []
        for row in table:
            formatted.append(self.format_row(row, widths, *args, **kwargs))
        return formatted

    def print_table(self, table, macro_name):
        formatted = self.format_table(table)
        print(  '//   %s\n' % formatted[0] +
                '#define %s(DO) \\\n' % macro_name +
                ' \\\n'.join(['  DO(%s)' % frow for frow in formatted[1:]]))

class db_sigpoint_gen(macro_table_gen):
    "A generator for SigPoint tables."
    def __init__(self, db):
        self.db = db

    def print_sigpoint_table(self):
        self.print_table(self.db.sigpoint_table, 'DO_SIGPOINTS')

    def print_interpretation_table(self):
        self.print_table(self.db.interpretation_table, 'DO_INTERPRETATION_TABLE')

    def print_content(self):
        self.print_sigpoint_table()
        self.print_interpretation_table()

class string_output:
    def __init__(self):
        self.val = ""
    def write(self, text):
        self.val = self.val + str(text)
    def __str__(self):
        return self.val

def run_with_stdout(fn):
    import sys
    _stdout_saved = sys.stdout
    so = string_output()
    try:
        sys.stdout = so
        fn()
    finally:
        sys.stdout = _stdout_saved
    return str(so)

def get_hlsl_intrinsic_stats():
    db = get_db_hlsl()
    longest_fn = db.intrinsics[0]
    longest_param = None
    longest_arglist_fn = db.intrinsics[0]
    for i in sorted(db.intrinsics, lambda x,y: cmp(x.key, y.key)):
        # Get some values for maximum lengths.
        if len(i.name) > len(longest_fn.name):
            longest_fn = i
        for p_idx, p in enumerate(i.params):
            if p_idx > 0 and (longest_param is None or len(p.name) > len(longest_param.name)):
                longest_param = p
        if len(i.params) > len(longest_arglist_fn.params):
            longest_arglist_fn = i
    result = ""
    for k in sorted(db.namespaces.keys()):
        v = db.namespaces[k]
        result += "static const UINT g_u%sCount = %d;\n" % (k, len(v.intrinsics))
    result += "\n"
    result += "static const int g_MaxIntrinsicName = %d; // Count of characters for longest intrinsic name - '%s'\n" % (len(longest_fn.name), longest_fn.name)
    result += "static const int g_MaxIntrinsicParamName = %d; // Count of characters for longest intrinsic parameter name - '%s'\n" % (len(longest_param.name), longest_param.name)
    result += "static const int g_MaxIntrinsicParamCount = %d; // Count of parameters (without return) for longest intrinsic argument list - '%s'\n" % (len(longest_arglist_fn.params) - 1, longest_arglist_fn.name)
    return result

def get_hlsl_intrinsics():
    db = get_db_hlsl()
    result = ""
    last_ns = ""
    ns_table = ""
    id_prefix = ""
    arg_idx = 0
    for i in sorted(db.intrinsics, lambda x,y: cmp(x.key, y.key)):
        if last_ns != i.ns:
            last_ns = i.ns
            id_prefix = "IOP" if last_ns == "Intrinsics" else "MOP"
            if (len(ns_table)):
                result += ns_table + "};\n"
            result += "\n//\n// Start of %s\n//\n\n" % (last_ns)
            # This used to be qualified as __declspec(selectany), but that's no longer necessary.
            ns_table = "static const HLSL_INTRINSIC g_%s[] =\n{\n" % (last_ns)
            arg_idx = 0
        ns_table += "    (UINT)hlsl::IntrinsicOp::%s_%s, %s, %s, %d, %d, g_%s_Args%s,\n" % (id_prefix, i.name, str(i.readonly).lower(), str(i.readnone).lower(), i.overload_param_index,len(i.params), last_ns, arg_idx)
        result += "static const HLSL_INTRINSIC_ARGUMENT g_%s_Args%s[] =\n{\n" % (last_ns, arg_idx)
        for p in i.params:
            result += "    \"%s\", %s, %s, %s, %s, %s, %s, %s,\n" % (
                p.name, p.param_qual, p.template_id, p.template_list,
                p.component_id, p.component_list, p.rows, p.cols)
        result += "};\n\n"
        arg_idx += 1
    result += ns_table + "};\n"
    return result

def enum_hlsl_intrinsics():
    db = get_db_hlsl()
    result = ""
    enumed = []
    for i in sorted(db.intrinsics, lambda x,y: cmp(x.key, y.key)):
        if (i.enum_name not in enumed):
            result += "  %s,\n" % (i.enum_name)
            enumed.append(i.enum_name)
    # unsigned
    result += "  // unsigned\n"

    for i in sorted(db.intrinsics, lambda x,y: cmp(x.key, y.key)):
        if (i.unsigned_op != ""):
          if (i.unsigned_op not in enumed):
            result += "  %s,\n" % (i.unsigned_op)
            enumed.append(i.unsigned_op)

    result += "  Num_Intrinsics,\n"
    return result

def has_unsigned_hlsl_intrinsics():
    db = get_db_hlsl()
    result = ""
    enumed = []
    # unsigned
    for i in sorted(db.intrinsics, lambda x,y: cmp(x.key, y.key)):
        if (i.unsigned_op != ""):
          if (i.enum_name not in enumed):
            result += "  case IntrinsicOp::%s:\n" % (i.enum_name)
            enumed.append(i.enum_name)
    return result

def get_unsigned_hlsl_intrinsics():
    db = get_db_hlsl()
    result = ""
    enumed = []
    # unsigned
    for i in sorted(db.intrinsics, lambda x,y: cmp(x.key, y.key)):
        if (i.unsigned_op != ""):
          if (i.enum_name not in enumed):
            enumed.append(i.enum_name)
            result += "  case IntrinsicOp::%s:\n" % (i.enum_name)
            result += "    return static_cast<unsigned>(IntrinsicOp::%s);\n" % (i.unsigned_op)
    return result

def get_oloads_props():
    db = get_db_dxil()
    gen = db_oload_gen(db)
    return run_with_stdout(lambda: gen.print_opfunc_props())
        
def get_oloads_funcs():
    db = get_db_dxil()
    gen = db_oload_gen(db)
    return run_with_stdout(lambda: gen.print_opfunc_table())

def get_enum_decl(name, **kwargs):
    db = get_db_dxil()
    gen = db_enumhelp_gen(db)
    return run_with_stdout(lambda: gen.print_enum(db.enum_idx[name], **kwargs))

def get_valrule_enum():
    return get_enum_decl("ValidationRule", hide_val=True)

def get_valrule_text():
    db = get_db_dxil()
    result = "switch(value) {\n"
    for v in db.enum_idx["ValidationRule"].values:
        result += "  case hlsl::ValidationRule::" + v.name + ": return \"" + v.err_msg + "\";\n"
    result += "}\n"
    return result

def get_instrhelper():
    db = get_db_dxil()
    gen = db_instrhelp_gen(db)
    return run_with_stdout(lambda: gen.print_body())

def get_instrs_pred(varname, pred, attr_name="dxil_opid"):
    db = get_db_dxil()
    if type(pred) == str:
        pred_fn = lambda i: getattr(i, pred)
    else:
        pred_fn = pred
    llvm_instrs = [i for i in db.instr if pred_fn(i)]
    result = format_comment("// ", "Instructions: %s" % ", ".join([i.name + "=" + str(getattr(i, attr_name)) for i in llvm_instrs]))
    result += "return %s;" % build_range_code(varname, [getattr(i, attr_name) for i in llvm_instrs])
    result += "\n"
    return result

def get_instrs_rst():
    "Create an rst table of allowed LLVM instructions."
    db = get_db_dxil()
    instrs = [i for i in db.instr if i.is_allowed and not i.is_dxil_op]
    instrs = sorted(instrs, key=lambda v : v.llvm_id)
    rows = []
    rows.append(["Instruction", "Action", "Operand overloads"])
    for i in instrs:
        rows.append([i.name, i.doc, i.oload_types])
    result = "\n\n" + format_rst_table(rows) + "\n\n"
    # Add detailed instruction information where available.
    for i in instrs:
        if i.remarks:
            result += i.name + "\n" + ("~" * len(i.name)) + "\n\n" + i.remarks + "\n\n"
    return result + "\n"

def get_init_passes():
    "Create a series of statements to initialize passes in a registry."
    db = db_dxil()
    result = ""
    for p in sorted(db.passes, key=lambda p : p.type_name):
        result += "initialize%sPass(Registry);\n" % p.type_name
    return result

def get_pass_arg_names():
    "Return an ArrayRef of argument names based on passName"
    db = db_dxil()
    decl_result = ""
    check_result = ""
    for p in sorted(db.passes, key=lambda p : p.type_name):
        if len(p.args):
            decl_result += "static const LPCSTR %sArgs[] = { " % p.type_name
            check_result += "if (strcmp(passName, \"%s\") == 0) return ArrayRef<LPCSTR>(%sArgs, _countof(%sArgs));\n" % (p.name, p.type_name, p.type_name)
            sep = ""
            for a in p.args:
                decl_result += sep + "\"%s\"" % a.name
                sep = ", "
            decl_result += " };\n"
    return decl_result + check_result

def get_pass_arg_descs():
    "Return an ArrayRef of argument descriptions based on passName"
    db = db_dxil()
    decl_result = ""
    check_result = ""
    for p in sorted(db.passes, key=lambda p : p.type_name):
        if len(p.args):
            decl_result += "static const LPCSTR %sArgs[] = { " % p.type_name
            check_result += "if (strcmp(passName, \"%s\") == 0) return ArrayRef<LPCSTR>(%sArgs, _countof(%sArgs));\n" % (p.name, p.type_name, p.type_name)
            sep = ""
            for a in p.args:
                decl_result += sep + "\"%s\"" % a.doc
                sep = ", "
            decl_result += " };\n"
    return decl_result + check_result

def get_is_pass_option_name():
    "Create a return expression to check whether a value 'S' is a pass option name."
    db = db_dxil()
    prefix = ""
    result = "return "
    for k in db.pass_idx_args:
        result += prefix + "S.equals(\"%s\")" % k
        prefix = "\n  ||  "
    return result + ";"

def get_opcodes_rst():
    "Create an rst table of opcodes"
    db = db_dxil()
    instrs = [i for i in db.instr if i.is_allowed and i.is_dxil_op]
    instrs = sorted(instrs, key=lambda v : v.dxil_opid)
    rows = []
    rows.append(["ID", "Name", "Description"])
    for i in instrs:
        rows.append([i.dxil_opid, i.dxil_op, i.doc])
    result = "\n\n" + format_rst_table(rows) + "\n\n"
    # Add detailed instruction information where available.
    instrs = sorted(instrs, key=lambda v : v.name)
    for i in instrs:
        if i.remarks:
            result += i.name + "\n" + ("~" * len(i.name)) + "\n\n" + i.remarks + "\n\n"
    return result + "\n"

def get_valrules_rst():
    "Create an rst table of validation rules instructions."
    db = db_dxil()
    rules = [i for i in db.val_rules if not i.is_disabled]
    rules = sorted(rules, key=lambda v : v.name)
    rows = []
    rows.append(["Rule Code", "Description"])
    for i in rules:
        rows.append([i.name, i.doc])
    return "\n\n" + format_rst_table(rows) + "\n\n"

def get_opsigs():
    # Create a list of DXIL operation signatures, sorted by ID.
    db = get_db_dxil()
    instrs = [i for i in db.instr if i.is_dxil_op]
    instrs = sorted(instrs, key=lambda v : v.dxil_opid)
    # db_dxil already asserts that the numbering is dense.
    # Create the code to write out.
    code = "static const char *OpCodeSignatures[] = {\n"
    for inst_idx,i in enumerate(instrs):
        code += "  \"("
        for operand in i.ops:
            if operand.pos > 1: # skip 0 (the return value) and 1 (the opcode itself)
                code += operand.name
                if operand.pos < len(i.ops) - 1:
                    code += ","
        code += ")\""
        if inst_idx < len(instrs) - 1:
            code += ","
        code += "  // " + i.name
        code += "\n"
    code += "};\n"
    return code

def get_valopcode_sm_text():
    db = get_db_dxil()
    instrs = [i for i in db.instr if i.is_dxil_op]
    instrs = sorted(instrs, key=lambda v : v.shader_models + "." + ("%4d" % v.dxil_opid))
    last_model = None
    model_instrs = []
    code = ""
    def flush_instrs(model_instrs, model_name):
        if len(model_instrs) == 0:
            return ""
        if model_name == "*": # don't write these out, instead fall through
            return ""
        result = format_comment("// ", "Instructions: %s" % ", ".join([i.name + "=" + str(i.dxil_opid) for i in model_instrs]))
        result += "if (" + build_range_code("op", [i.dxil_opid for i in model_instrs]) + ")\n"
        result += "  return "
        if last_model == "*":
            result += "true"
        else:
            for code_idx,code in enumerate(last_model):
                if code_idx > 0:
                    result += " || "
                result += "pSM->Is" + code.upper() + "S()"
        result += ";\n"
        return result

    for i in instrs:
        if i.shader_models <> last_model:
            code += flush_instrs(model_instrs, last_model)
            model_instrs = []
            last_model = i.shader_models
        model_instrs.append(i)
    code += flush_instrs(model_instrs, last_model)
    code += "return true;\n"
    return code

def get_sigpoint_table():
    db = get_db_dxil()
    gen = db_sigpoint_gen(db)
    return run_with_stdout(lambda: gen.print_sigpoint_table())

def get_sigpoint_rst():
    "Create an rst table for SigPointKind."
    db = get_db_dxil()
    rows = [row[:] for row in db.sigpoint_table[:-1]]   # Copy table
    e = dict([(v.name, v) for v in db.enum_idx['SigPointKind'].values])
    rows[0] = ['ID'] + rows[0] + ['Description']
    for i in range(1, len(rows)):
        row = rows[i]
        v = e[row[0]]
        rows[i] = [v.value] + row + [v.doc]
    return "\n\n" + format_rst_table(rows) + "\n\n"

def get_sem_interpretation_enum_rst():
    db = get_db_dxil()
    rows = ([['ID', 'Name', 'Description']] +
            [[v.value, v.name, v.doc]
             for v in db.enum_idx['SemanticInterpretationKind'].values[:-1]])
    return "\n\n" + format_rst_table(rows) + "\n\n"

def get_sem_interpretation_table_rst():
    db = get_db_dxil()
    return "\n\n" + format_rst_table(db.interpretation_table) + "\n\n"

def get_interpretation_table():
    db = get_db_dxil()
    gen = db_sigpoint_gen(db)
    return run_with_stdout(lambda: gen.print_interpretation_table())


def RunCodeTagUpdate(file_path):
    import os
    import CodeTags
    print(" ... updating " + file_path)
    args = [file_path, file_path + ".tmp"]
    result = CodeTags.main(args)
    if result != 0:
        print(" ... error: %d" % result)
    else:
        with open(file_path, 'rt') as f:
            before = f.read()
        with open(file_path + ".tmp", 'rt') as f:
            after = f.read()
        if before == after:
            print("  --- no changes found")
        else:
            print("  +++ changes found, updating file")
            with open(file_path, 'wt') as f:
                f.write(after)
        os.remove(file_path + ".tmp")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate code to handle instructions.")
    parser.add_argument("-gen", choices=["docs-ref", "docs-spec", "inst-header", "enums", "oloads", "valfns"], help="Output type to generate.")
    parser.add_argument("-update-files", action="store_const", const=True)
    args = parser.parse_args()
    
    db = get_db_dxil() # used by all generators, also handy to have it run validation

    if args.gen == "docs-ref":
        gen = db_docsref_gen(db)
        gen.print_content()

    if args.gen == "docs-spec":
        import os, docutils.core
        assert "HLSL_SRC_DIR" in os.environ, "Environment variable HLSL_SRC_DIR is not defined"
        hlsl_src_dir = os.environ["HLSL_SRC_DIR"]
        spec_file = os.path.abspath(os.path.join(hlsl_src_dir, "docs/DXIL.rst"))
        with open(spec_file) as f:
            s = docutils.core.publish_file(f, writer_name="html")

    if args.gen == "inst-header":
        gen = db_instrhelp_gen(db)
        gen.print_content()

    if args.gen == "enums":
        gen = db_enumhelp_gen(db)
        gen.print_content()

    if args.gen == "oloads":
        gen = db_oload_gen(db)
        gen.print_content()

    if args.gen == "valfns":
        gen = db_valfns_gen(db)
        gen.print_content()

    if args.update_files:
        print("Updating files ...")
        import CodeTags
        import os
        
        assert "HLSL_SRC_DIR" in os.environ, "Environment variable HLSL_SRC_DIR is not defined"
        hlsl_src_dir = os.environ["HLSL_SRC_DIR"]
        pj = lambda *parts: os.path.abspath(os.path.join(*parts))
        files = [
            'docs/DXIL.rst',
            'lib/HLSL/DXILOperations.cpp',
            'include/dxc/HLSL/DXILConstants.h',
            'include/dxc/HLSL/DxilValidation.h',
            'include/dxc/HLSL/DxilInstructions.h',
            'lib/HLSL/DxcOptimizer.cpp',
            'lib/HLSL/DxilValidation.cpp',
            'tools/clang/lib/Sema/gen_intrin_main_tables_15.h',
            'include/dxc/HlslIntrinsicOp.h',
            'tools/clang/tools/dxcompiler/dxcompilerobj.cpp',
            'lib/HLSL/DxilSigPoint.cpp',
            ]
        for relative_file_path in files:
            RunCodeTagUpdate(pj(hlsl_src_dir, relative_file_path))