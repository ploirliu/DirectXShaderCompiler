//===--- BackendUtil.h - LLVM Backend Utilities -----------------*- C++ -*-===//
///////////////////////////////////////////////////////////////////////////////
//                                                                           //
// BackendUtil.h                                                             //
// Copyright (C) Microsoft Corporation. All rights reserved.                 //
// Licensed under the MIT license. See COPYRIGHT in the project root for     //
// full license information.                                                 //
//                                                                           //
///////////////////////////////////////////////////////////////////////////////

#ifndef LLVM_CLANG_CODEGEN_BACKENDUTIL_H
#define LLVM_CLANG_CODEGEN_BACKENDUTIL_H

#include "clang/Basic/LLVM.h"

namespace llvm {
  class Module;
}

namespace clang {
  class DiagnosticsEngine;
  class CodeGenOptions;
  class TargetOptions;
  class LangOptions;

  enum BackendAction {
    Backend_EmitAssembly,  ///< Emit native assembly files
    Backend_EmitBC,        ///< Emit LLVM bitcode files
    Backend_EmitLL,        ///< Emit human-readable LLVM assembly
    Backend_EmitNothing,   ///< Don't emit anything (benchmarking mode)
    Backend_EmitMCNull,    ///< Run CodeGen, but don't emit anything
    Backend_EmitObj,       ///< Emit native object files
    Backend_EmitPasses     ///< Emit pass configuration - HLSL Change
  };

  void EmitBackendOutput(DiagnosticsEngine &Diags, const CodeGenOptions &CGOpts,
                         const TargetOptions &TOpts, const LangOptions &LOpts,
                         StringRef TDesc, llvm::Module *M, BackendAction Action,
                         raw_pwrite_stream *OS);
}

#endif