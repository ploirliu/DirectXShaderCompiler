///////////////////////////////////////////////////////////////////////////////
//                                                                           //
// dxcapi.h                                                                  //
// Copyright (C) Microsoft Corporation. All rights reserved.                 //
// Licensed under the MIT license. See COPYRIGHT in the project root for     //
// full license information.                                                 //
//                                                                           //
// Provides declarations for the DirectX Compiler API entry point.           //
//                                                                           //
///////////////////////////////////////////////////////////////////////////////

#ifndef __DXC_API__
#define __DXC_API__

#ifndef DXC_API_IMPORT
#define DXC_API_IMPORT __declspec(dllimport)
#endif

struct IDxcIncludeHandler;

/// <summary>
/// Creates a single uninitialized object of the class associated with a specified CLSID.
/// </summary>
/// <param name="rclsid">
/// The CLSID associated with the data and code that will be used to create the object.
/// </param>
/// <param name="riid">
/// A reference to the identifier of the interface to be used to communicate 
/// with the object.
/// </param>
/// <param name="ppv">
/// Address of pointer variable that receives the interface pointer requested
/// in riid. Upon successful return, *ppv contains the requested interface
/// pointer. Upon failure, *ppv contains NULL.</param>
/// <remarks>
/// While this function is similar to CoCreateInstance, there is no COM involvement.
/// </remarks>
typedef HRESULT (__stdcall *DxcCreateInstanceProc)(
    _In_ REFCLSID   rclsid,
    _In_ REFIID     riid,
    _Out_ LPVOID*   ppv
);

/// <summary>
/// Creates a single uninitialized object of the class associated with a specified CLSID.
/// </summary>
/// <param name="rclsid">
/// The CLSID associated with the data and code that will be used to create the object.
/// </param>
/// <param name="riid">
/// A reference to the identifier of the interface to be used to communicate 
/// with the object.
/// </param>
/// <param name="ppv">
/// Address of pointer variable that receives the interface pointer requested
/// in riid. Upon successful return, *ppv contains the requested interface
/// pointer. Upon failure, *ppv contains NULL.</param>
/// <remarks>
/// While this function is similar to CoCreateInstance, there is no COM involvement.
/// </remarks>
DXC_API_IMPORT HRESULT __stdcall DxcCreateInstance(
  _In_ REFCLSID   rclsid,
  _In_ REFIID     riid,
  _Out_ LPVOID*   ppv
  );


// IDxcBlob is an alias of ID3D10Blob and ID3DBlob
struct __declspec(uuid("8BA5FB08-5195-40e2-AC58-0D989C3A0102"))
IDxcBlob : public IUnknown {
public:
  virtual LPVOID STDMETHODCALLTYPE GetBufferPointer(void) = 0;
  virtual SIZE_T STDMETHODCALLTYPE GetBufferSize(void) = 0;
};

struct __declspec(uuid("7241d424-2646-4191-97c0-98e96e42fc68"))
IDxcBlobEncoding : public IDxcBlob {
public:
  virtual HRESULT STDMETHODCALLTYPE GetEncoding(_Out_ BOOL *pKnown,
                                                _Out_ UINT32 *pCodePage) = 0;
};

struct __declspec(uuid("e5204dc7-d18c-4c3c-bdfb-851673980fe7"))
IDxcLibrary : public IUnknown {
  virtual HRESULT STDMETHODCALLTYPE SetMalloc(_In_opt_ IMalloc *pMalloc) = 0;
  virtual HRESULT STDMETHODCALLTYPE CreateBlobFromBlob(
    _In_ IDxcBlob *pBlob, UINT32 offset, UINT32 length, _COM_Outptr_ IDxcBlob **ppResult) = 0;
  virtual HRESULT STDMETHODCALLTYPE CreateBlobFromFile(
    LPCWSTR pFileName, _In_opt_ UINT32* codePage,
    _COM_Outptr_ IDxcBlobEncoding **pBlobEncoding) = 0;
  virtual HRESULT STDMETHODCALLTYPE CreateBlobWithEncodingFromPinned(
    LPBYTE pText, UINT32 size, UINT32 codePage,
    _COM_Outptr_ IDxcBlobEncoding **pBlobEncoding) = 0;
  virtual HRESULT STDMETHODCALLTYPE CreateBlobWithEncodingOnHeapCopy(
       _In_bytecount_(size) LPCVOID pText, UINT32 size, UINT32 codePage,
      _COM_Outptr_ IDxcBlobEncoding **pBlobEncoding) = 0;
  virtual HRESULT STDMETHODCALLTYPE CreateBlobWithEncodingOnMalloc(
    _In_bytecount_(size) LPCVOID pText, IMalloc *pIMalloc, UINT32 size, UINT32 codePage,
    _COM_Outptr_ IDxcBlobEncoding **pBlobEncoding) = 0;
  virtual HRESULT STDMETHODCALLTYPE CreateIncludeHandler(
      _COM_Outptr_ IDxcIncludeHandler **ppResult) = 0;
  virtual HRESULT STDMETHODCALLTYPE CreateStreamFromBlobReadOnly(
      _In_ IDxcBlob *pBlob, _COM_Outptr_ IStream **ppStream) = 0;
  virtual HRESULT STDMETHODCALLTYPE GetBlobAsUtf8(
      _In_ IDxcBlob *pBlob, _COM_Outptr_ IDxcBlobEncoding **pBlobEncoding) = 0;
  virtual HRESULT STDMETHODCALLTYPE GetBlobAsUtf16(
      _In_ IDxcBlob *pBlob, _COM_Outptr_ IDxcBlobEncoding **pBlobEncoding) = 0;
};

struct __declspec(uuid("CEDB484A-D4E9-445A-B991-CA21CA157DC2"))
IDxcOperationResult : public IUnknown {
  virtual HRESULT STDMETHODCALLTYPE GetStatus(_Out_ HRESULT *pStatus) = 0;
  virtual HRESULT STDMETHODCALLTYPE GetResult(_COM_Outptr_result_maybenull_ IDxcBlob **pResult) = 0;
  virtual HRESULT STDMETHODCALLTYPE GetErrorBuffer(_COM_Outptr_result_maybenull_ IDxcBlobEncoding **pErrors) = 0;
};

struct __declspec(uuid("7f61fc7d-950d-467f-b3e3-3c02fb49187c"))
IDxcIncludeHandler : public IUnknown {
  virtual HRESULT STDMETHODCALLTYPE LoadSource(
    _In_ LPCWSTR pFilename,                                   // Candidate filename.
    _COM_Outptr_result_maybenull_ IDxcBlob **ppIncludeSource  // Resultant source object for included file, nullptr if not found.
    ) = 0;
};

struct DxcDefine {
  LPCWSTR Name;
  _Maybenull_ LPCWSTR Value;
};

struct __declspec(uuid("8c210bf3-011f-4422-8d70-6f9acb8db617"))
IDxcCompiler : public IUnknown {
  // Compile a single entry point to the target shader model
  virtual HRESULT STDMETHODCALLTYPE Compile(
    _In_ IDxcBlob *pSource,                       // Source text to compile
    _In_opt_ LPCWSTR pSourceName,                 // Optional file name for pSource. Used in errors and include handlers.
    _In_ LPCWSTR pEntryPoint,                     // entry point name
    _In_ LPCWSTR pTargetProfile,                  // shader profile to compile
    _In_count_(argCount) LPCWSTR *pArguments,     // Array of pointers to arguments
    _In_ UINT32 argCount,                         // Number of arguments
    _In_count_(defineCount) const DxcDefine *pDefines,  // Array of defines
    _In_ UINT32 defineCount,                      // Number of defines
    _In_opt_ IDxcIncludeHandler *pIncludeHandler, // user-provided interface to handle #include directives (optional)
    _COM_Outptr_ IDxcOperationResult **ppResult   // Compiler output status, buffer, and errors
  ) = 0;

  // Preprocess source text
  virtual HRESULT STDMETHODCALLTYPE Preprocess(
    _In_ IDxcBlob *pSource,                       // Source text to preprocess
    _In_opt_ LPCWSTR pSourceName,                 // Optional file name for pSource. Used in errors and include handlers.
    _In_count_(argCount) LPCWSTR *pArguments,     // Array of pointers to arguments
    _In_ UINT32 argCount,                         // Number of arguments
    _In_count_(defineCount) const DxcDefine *pDefines,  // Array of defines
    _In_ UINT32 defineCount,                      // Number of defines
    _In_opt_ IDxcIncludeHandler *pIncludeHandler, // user-provided interface to handle #include directives (optional)
    _COM_Outptr_ IDxcOperationResult **ppResult   // Preprocessor output status, buffer, and errors
  ) = 0;

  virtual HRESULT STDMETHODCALLTYPE Disassemble(
    _In_ IDxcBlob *pSource,                         // Program to disassemble.
    _COM_Outptr_ IDxcBlobEncoding **ppDisassembly   // Disassembly text.
    ) = 0;
};

static const UINT32 DxcValidatorFlags_Default = 0;
static const UINT32 DxcValidatorFlags_InPlaceEdit = 1;  // Validator is allowed to update shader blob in-place.
static const UINT32 DxcValidatorFlags_ValidMask = 0x1;

struct __declspec(uuid("A6E82BD2-1FD7-4826-9811-2857E797F49A"))
IDxcValidator : public IUnknown {
  // Validate a shader.
  virtual HRESULT STDMETHODCALLTYPE Validate(
    _In_ IDxcBlob *pShader,                       // Shader to validate.
    _In_ UINT32 Flags,                            // Validation flags.
    _COM_Outptr_ IDxcOperationResult **ppResult   // Validation output status, buffer, and errors
    ) = 0;
};

struct __declspec(uuid("091f7a26-1c1f-4948-904b-e6e3a8a771d5"))
IDxcAssembler : public IUnknown {
  // Assemble dxil in ll or llvm bitcode to DXIL container.
  virtual HRESULT STDMETHODCALLTYPE AssembleToContainer(
    _In_ IDxcBlob *pShader,                       // Shader to assemble.
    _COM_Outptr_ IDxcOperationResult **ppResult   // Assembly output status, buffer, and errors
    ) = 0;
};

struct __declspec(uuid("d2c21b26-8350-4bdc-976a-331ce6f4c54c"))
IDxcContainerReflection : public IUnknown {
  virtual HRESULT STDMETHODCALLTYPE Load(_In_ IDxcBlob *pContainer) = 0; // Container to load.
  virtual HRESULT STDMETHODCALLTYPE GetPartCount(_Out_ UINT32 *pResult) = 0;
  virtual HRESULT STDMETHODCALLTYPE GetPartKind(UINT32 idx, _Out_ UINT32 *pResult) = 0;
  virtual HRESULT STDMETHODCALLTYPE GetPartContent(UINT32 idx, _COM_Outptr_ IDxcBlob **ppResult) = 0;
  virtual HRESULT STDMETHODCALLTYPE FindFirstPartKind(UINT32 kind, _Out_ UINT32 *pResult) = 0;
  virtual HRESULT STDMETHODCALLTYPE GetPartReflection(UINT32 idx, REFIID iid, void **ppvObject) = 0;
};

struct __declspec(uuid("AE2CD79F-CC22-453F-9B6B-B124E7A5204C"))
IDxcOptimizerPass : public IUnknown {
  virtual HRESULT STDMETHODCALLTYPE GetOptionName(_COM_Outptr_ LPWSTR *ppResult) = 0;
  virtual HRESULT STDMETHODCALLTYPE GetDescription(_COM_Outptr_ LPWSTR *ppResult) = 0;
  virtual HRESULT STDMETHODCALLTYPE GetOptionArgCount(_Out_ UINT32 *pCount) = 0;
  virtual HRESULT STDMETHODCALLTYPE GetOptionArgName(UINT32 argIndex, _COM_Outptr_ LPWSTR *ppResult) = 0;
  virtual HRESULT STDMETHODCALLTYPE GetOptionArgDescription(UINT32 argIndex, _COM_Outptr_ LPWSTR *ppResult) = 0;
};

struct __declspec(uuid("25740E2E-9CBA-401B-9119-4FB42F39F270"))
IDxcOptimizer : public IUnknown {
  virtual HRESULT STDMETHODCALLTYPE GetAvailablePassCount(_Out_ UINT32 *pCount) = 0;
  virtual HRESULT STDMETHODCALLTYPE GetAvailablePass(UINT32 index, _COM_Outptr_ IDxcOptimizerPass** ppResult) = 0;
  virtual HRESULT STDMETHODCALLTYPE RunOptimizer(IDxcBlob *pBlob,
    _In_count_(optionCount) LPCWSTR *ppOptions, UINT32 optionCount,
    _COM_Outptr_ IDxcBlob **pOutputModule,
    _COM_Outptr_opt_ IDxcBlobEncoding **ppOutputText) = 0;
};

static const UINT32 DxcVersionInfoFlags_None = 0;
static const UINT32 DxcVersionInfoFlags_Debug = 1; // Matches VS_FF_DEBUG

struct __declspec(uuid("b04f5b50-2059-4f12-a8ff-a1e0cde1cc7e"))
IDxcVersionInfo : public IUnknown {
  virtual HRESULT STDMETHODCALLTYPE GetVersion(_Out_ UINT32 *pMajor, _Out_ UINT32 *pMinor) = 0;
  virtual HRESULT STDMETHODCALLTYPE GetFlags(_Out_ UINT32 *pFlags) = 0;
};

// {73e22d93-e6ce-47f3-b5bf-f0664f39c1b0}
__declspec(selectany) extern const CLSID CLSID_DxcCompiler = {
  0x73e22d93,
  0xe6ce,
  0x47f3,
  { 0xb5, 0xbf, 0xf0, 0x66, 0x4f, 0x39, 0xc1, 0xb0 }
};

// {CD1F6B73-2AB0-484D-8EDC-EBE7A43CA09F}
__declspec(selectany) extern const CLSID CLSID_DxcDiaDataSource = {
  0xcd1f6b73,
  0x2ab0,
  0x484d,
  { 0x8e, 0xdc, 0xeb, 0xe7, 0xa4, 0x3c, 0xa0, 0x9f }
};

// {6245D6AF-66E0-48FD-80B4-4D271796748C}
__declspec(selectany) extern const GUID CLSID_DxcLibrary = {
  0x6245d6af,
  0x66e0,
  0x48fd,
  { 0x80, 0xb4, 0x4d, 0x27, 0x17, 0x96, 0x74, 0x8c }
};

// {8CA3E215-F728-4CF3-8CDD-88AF917587A1}
__declspec(selectany) extern const GUID CLSID_DxcValidator = {
  0x8ca3e215,
  0xf728,
  0x4cf3,
  { 0x8c, 0xdd, 0x88, 0xaf, 0x91, 0x75, 0x87, 0xa1 }
};

// {D728DB68-F903-4F80-94CD-DCCF76EC7151}
__declspec(selectany) extern const GUID CLSID_DxcAssembler = {
  0xd728db68,
  0xf903,
  0x4f80,
  { 0x94, 0xcd, 0xdc, 0xcf, 0x76, 0xec, 0x71, 0x51 }
};

// {b9f54489-55b8-400c-ba3a-1675e4728b91}
__declspec(selectany) extern const GUID CLSID_DxcContainerReflection = {
  0xb9f54489,
  0x55b8,
  0x400c,
  { 0xba, 0x3a, 0x16, 0x75, 0xe4, 0x72, 0x8b, 0x91 }
};

// {AE2CD79F-CC22-453F-9B6B-B124E7A5204C}
__declspec(selectany) extern const GUID CLSID_DxcOptimizer = {
    0xae2cd79f,
    0xcc22,
    0x453f,
    {0x9b, 0x6b, 0xb1, 0x24, 0xe7, 0xa5, 0x20, 0x4c}
};

#endif