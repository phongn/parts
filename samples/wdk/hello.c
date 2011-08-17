#include <ntddk.h> 

NTSTATUS DriverEntry(PDRIVER_OBJECT DriverObject, PUNICODE_STRING RegistryPath) 
{
    DbgPrint("Hello, World\n");

    return STATUS_SUCCESS; 
}

/* vim: set et ts=4 sw=4 ai */

