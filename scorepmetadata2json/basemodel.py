from typing import List, Optional, Dict
from pydantic import BaseModel, Field


class Executable(BaseModel):
    compiler: str = Field(..., description="The compiler name.")
    define_flags: Optional[List[str]] = Field(None, description="The define flags.")
    compiler_flags: Optional[List[str]] = Field(None, description="The compiler flags.")
    library_files: Optional[List[str]] = Field(None, description="The library files.")
    object_files: Optional[List[str]] = Field(None, description="The object files.")
    env: Optional[Dict[str, Optional[str]]] = Field(
        None, description="The environment variables."
    )


class Object(BaseModel):
    compiler: str = Field(..., description="The compiler name.")
    source_language: str = Field(..., description="The source language.")

    define_flags: Optional[List[str]] = Field(None, description="The define flags.")
    compiler_flags: Optional[List[str]] = Field(None, description="The compiler flags.")
    library_files: Optional[List[str]] = Field(None, description="The library files.")
    source_files: Optional[List[str]] = Field(None, description="The source files.")
    env: Optional[Dict[str, Optional[str]]] = Field(
        None, description="The environment variables."
    )


class Instrumenter(BaseModel):
    executable: Optional[Executable] = Field(
        None, description="The executable metadata."
    )
    object: Optional[List[Object]] = Field(None, description="The object metadata.")


class Runtime(BaseModel):
    env: Optional[Dict[str, Optional[str]]] = Field(
        None, description="The environment variables."
    )


class Metadata(BaseModel):
    runtime: Optional[Runtime] = Field(None, description="The runtime metadata.")
    instrumenter: Optional[Instrumenter] = Field(
        None, description="The instrumenter metadata."
    )
