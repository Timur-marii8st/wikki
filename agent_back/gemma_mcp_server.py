import asyncio
import os
import sys
import signal
import shutil
import glob

from typing import Dict, List, Optional, Any
from fastmcp import FastMCP
import aiofiles

from document_editing_tools import (create_pdf_from_text, merge_pdfs,
                                    extract_pdf_pages, create_docx, add_text_to_docx, replace_text_in_docx, create_pptx,
                                    add_slide_to_pptx, create_xlsx, write_to_excel_cell, read_from_excel_cell, 
                                    write_data_to_excel_range)

from gemma_mcp_client import GemmaMCPClient, FunctionDefinition

# Print startup message
print("[fastfs-mcp] Server starting...", file=sys.stderr, flush=True)

# Set the default workspace directory to the parent directory
WORKSPACE_DIR = os.path.join(os.getcwd(), 'workspace')

if os.path.exists(WORKSPACE_DIR):
    os.chdir(WORKSPACE_DIR)
    print(f"[fastfs-mcp] Working directory set to {WORKSPACE_DIR}", file=sys.stderr, flush=True)
else:
    current_dir = os.getcwd()
    print(f"[fastfs-mcp] Warning: {WORKSPACE_DIR} not found, using current directory: {current_dir}", file=sys.stderr, flush=True)

# Initialize the MCP server
mcp = FastMCP(name="fastfs-mcp")

async def run_command(cmd: List[str], input_text: Optional[str] = None) -> Dict[str, Any]:
    """ Execute command asinc. and return the result in JSON."""
    try:
        print(f"[DEBUG] Running command: {cmd}", file=sys.stderr, flush=True)
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE if input_text else None,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate(input_text.encode() if input_text else None)
        result = {
            "returncode": process.returncode,
            "stdout": stdout.decode().strip(),
            "stderr": stderr.decode().strip(),
        }
        if process.returncode == 0:
            return {"success": True, **result}
        else:
            print(f"[ERROR] Command failed: {result['stderr']}", file=sys.stderr, flush=True)
            return {"success": False, **result}
    except Exception as e:
        print(f"[ERROR] Exception running command: {str(e)}", file=sys.stderr, flush=True)
        return {"success": False, "exception": str(e)}

# Define tool schemas with proper typing and input validation
@mcp.tool(description="List files and directories at a given path.")
async def ls(path: str = ".") -> Dict[str, Any]:
    try:
        print(f"[DEBUG] ls called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"Path '{path}' does not exist"}
        return {"files": os.listdir(path)}
    except Exception as e:
        print(f"[ERROR] ls failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Print the current working directory.")
async def pwd() -> Dict[str, Any]:
    try:
        print(f"[DEBUG] pwd called", file=sys.stderr, flush=True)
        return {"cwd": os.getcwd()}
    except Exception as e:
        print(f"[ERROR] pwd failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Change the current working directory.")
async def cd(path: str) -> Dict[str, Any]:
    try:
        print(f"[DEBUG] cd called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"Path '{path}' does not exist"}
        if not os.path.isdir(path):
            return {"error": f"'{path}' is not a directory"}
        os.chdir(path)
        return {"cwd": os.getcwd()}
    except Exception as e:
        print(f"[ERROR] cd failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Read the contents of a file.")
async def read(path: str) -> Dict[str, Any]:
    try:
        print(f"[DEBUG] read called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"File '{path}' does not exist"}
        if not os.path.isfile(path):
            return {"error": f"'{path}' is not a file"}
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            content = await f.read()
        return {"content": content}
    except Exception as e:
        print(f"[ERROR] read failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Write contents to a file.")
async def write(path: str, content: str = "") -> Dict[str, Any]:
    try:
        print(f"[DEBUG] write called with path: {path}", file=sys.stderr, flush=True)
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
        async with aiofiles.open(path, 'w', encoding='utf-8') as f:
            await f.write(content)
        return {"success": True, "path": path}
    except Exception as e:
        print(f"[ERROR] write failed: {str(e)}", file=sys.stderr, flush=True)
        return {"success": False, "error": str(e)}

@mcp.tool(description="Search for a pattern in a file.")
async def grep(pattern: str, path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"error": f"File '{path}' does not exist"}
    if not os.path.isfile(path):
        return {"error": f"'{path}' is not a file"}
    cmd = ["grep", "-n", pattern, path]
    result = await run_command(cmd)
    return result

@mcp.tool(description="Locate a command in the system path.")
async def which(command: str) -> Dict[str, Any]:
    cmd = ["which", command]
    result = await run_command(cmd)
    return result

@mcp.tool(description="Use sed to transform file content using stream editing.")
async def sed(script: str, path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"error": f"File '{path}' does not exist"}
    if not os.path.isfile(path):
        return {"error": f"'{path}' is not a file"}
    cmd = ["sed", script, path]
    result = await run_command(cmd)
    return result

@mcp.tool(description="Use gawk to process file content using AWK scripting.")
async def gawk(script: str, path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        return {"error": f"File '{path}' does not exist"}
    if not os.path.isfile(path):
        return {"error": f"'{path}' is not a file"}
    cmd = ["gawk", script, path]
    result = await run_command(cmd)
    return result

# ===== ADDITIONAL FILESYSTEM TOOLS =====

@mcp.tool(description="Display file status (metadata).")
def stat(path: str) -> Dict[str, Any]:
    """Display file status and metadata."""
    import stat
    try:
        print(f"[DEBUG] stat called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"Path '{path}' does not exist"}
        
        st = os.stat(path)
        result = {
            "path": path,
            "size": st.st_size,
            "mode": stat.filemode(st.st_mode),
            "mode_octal": oct(st.st_mode)[-3:],
            "inode": st.st_ino,
            "device": st.st_dev,
            "links": st.st_nlink,
            "uid": st.st_uid,
            "gid": st.st_gid,
            "access_time": st.st_atime,
            "modification_time": st.st_mtime,
            "change_time": st.st_ctime,
            "is_file": os.path.isfile(path),
            "is_dir": os.path.isdir(path),
            "is_link": os.path.islink(path)
        }
        return result
    except Exception as e:
        print(f"[ERROR] stat failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Display directory tree structure.")
async def tree(path: str = ".", depth: int = 3) -> Dict[str, Any]:
    try:
        print(f"[DEBUG] tree called with path: {path}, depth: {depth}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"Path '{path}' does not exist"}
        cmd = ["tree", "-L", str(depth), path]
        result = await run_command(cmd)
        return result
    except Exception as e:
        print(f"[ERROR] tree failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Find files by pattern.")
async def find(path: str = ".", pattern: str = "*", file_type: str = "", max_depth: int = -1) -> Dict[str, Any]:
    try:
        print(f"[DEBUG] find called with path: {path}, pattern: {pattern}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"Path '{path}' does not exist"}
        cmd = ["find", path]
        if max_depth != -1:
            cmd.extend(["-maxdepth", str(max_depth)])
        if file_type and file_type in ['f', 'd', 'l', 'b', 'c', 'p', 's']:
            cmd.extend(["-type", file_type])
        elif file_type:
            return {"error": f"Invalid file type '{file_type}'"}
        cmd.extend(["-name", pattern])
        result = await run_command(cmd)
        if result.get("success") and result.get("stdout"):
            files = result["stdout"].split('\n')
        else:
            files = []
        return {"files": files, **result}
    except Exception as e:
        print(f"[ERROR] find failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Copy files or directories.")
def cp(source: str, destination: str, recursive: bool = False) -> str:
    """Copy files or directories."""
    try:
        print(f"[DEBUG] cp called with source: {source}, destination: {destination}", file=sys.stderr, flush=True)
        if not os.path.exists(source):
            return f"Error: Source '{source}' does not exist"
        
        if os.path.isdir(source) and not recursive:
            return f"Error: Source '{source}' is a directory, use recursive=True to copy directories"
        
        if recursive:
            shutil.copytree(source, destination)
            return f"Successfully copied directory '{source}' to '{destination}'"
        else:
            shutil.copy2(source, destination)
            return f"Successfully copied file '{source}' to '{destination}'"
    except Exception as e:
        print(f"[ERROR] cp failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Move or rename files or directories.")
def mv(source: str, destination: str) -> str:
    """Move or rename files or directories."""
    try:
        print(f"[DEBUG] mv called with source: {source}, destination: {destination}", file=sys.stderr, flush=True)
        if not os.path.exists(source):
            return f"Error: Source '{source}' does not exist"
        
        shutil.move(source, destination)
        return f"Successfully moved '{source}' to '{destination}'"
    except Exception as e:
        print(f"[ERROR] mv failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Remove files or directories.")
def rm(path: str, recursive: bool = False, force: bool = False) -> str:
    """Remove files or directories."""
    try:
        print(f"[DEBUG] rm called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            if force:
                return f"Warning: Path '{path}' does not exist, nothing removed"
            else:
                return f"Error: Path '{path}' does not exist"
        
        if os.path.isdir(path):
            if not recursive:
                return f"Error: '{path}' is a directory, use recursive=True to remove directories"
            shutil.rmtree(path)
            return f"Successfully removed directory '{path}'"
        else:
            os.remove(path)
            return f"Successfully removed file '{path}'"
    except Exception as e:
        print(f"[ERROR] rm failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Create a new empty file or update its timestamp.")
def touch(path: str) -> str:
    """Create a new empty file or update its timestamp."""
    try:
        print(f"[DEBUG] touch called with path: {path}", file=sys.stderr, flush=True)
        directory = os.path.dirname(path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)
            
        with open(path, 'a'):
            os.utime(path, None)
        return f"Successfully touched '{path}'"
    except Exception as e:
        print(f"[ERROR] touch failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Create a new directory.")
def mkdir(path: str, parents: bool = False) -> str:
    """Create a new directory."""
    try:
        print(f"[DEBUG] mkdir called with path: {path}", file=sys.stderr, flush=True)
        if os.path.exists(path):
            return f"Error: Path '{path}' already exists"
        
        if parents:
            os.makedirs(path)
        else:
            os.mkdir(path)
        return f"Successfully created directory '{path}'"
    except Exception as e:
        print(f"[ERROR] mkdir failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Show disk usage of a directory.")
async def du(path: str = ".", human_readable: bool = True, max_depth: int = 1) -> Dict[str, Any]:
    try:
        print(f"[DEBUG] du called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"Path '{path}' does not exist"}
        cmd = ["du"]
        if human_readable:
            cmd.append("-h")
        cmd.extend(["-d", str(max_depth), path])
        result = await run_command(cmd)
        return result
    except Exception as e:
        print(f"[ERROR] du failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Show disk space and usage.")
async def df(human_readable: bool = True) -> Dict[str, Any]:
    try:
        print(f"[DEBUG] df called", file=sys.stderr, flush=True)
        cmd = ["df"]
        if human_readable:
            cmd.append("-h")
        result = await run_command(cmd)
        return result
    except Exception as e:
        print(f"[ERROR] df failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Change file mode (permissions).")
async def chmod(path: str, mode: str) -> Dict[str, Any]:
    try:
        print(f"[DEBUG] chmod called with path: {path}, mode: {mode}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"Path '{path}' does not exist"}
        if mode.isdigit() and len(mode) <= 4:
            mode_int = int(mode, 8)
            os.chmod(path, mode_int)
            return {"success": True, "path": path, "mode": mode}
        else:
            cmd = ["chmod", mode, path]
            result = await run_command(cmd)
            return result
    except Exception as e:
        print(f"[ERROR] chmod failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Change file owner and group.")
async def chown(path: str, owner: str, group: Optional[str] = None) -> Dict[str, Any]:
    try:
        print(f"[DEBUG] chown called with path: {path}, owner: {owner}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"Path '{path}' does not exist"}
        owner_group = owner if group is None else f"{owner}:{group}"
        cmd = ["chown", owner_group, path]
        result = await run_command(cmd)
        return result
    except Exception as e:
        print(f"[ERROR] chown failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Concatenate and display file contents.")
def cat(paths: List[str]) -> str:
    """Concatenate and display file contents."""
    try:
        print(f"[DEBUG] cat called with paths: {paths}", file=sys.stderr, flush=True)
        result = ""
        
        for path in paths:
            if not os.path.exists(path):
                return f"Error: File '{path}' does not exist"
            if not os.path.isfile(path):
                return f"Error: '{path}' is not a file"
            
            with open(path, 'r', encoding='utf-8') as f:
                result += f.read()
                
        return result
    except Exception as e:
        print(f"[ERROR] cat failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Display the first part of files.")
def head(path: str, lines: int = 10) -> str:
    """Display the first part of files."""
    try:
        print(f"[DEBUG] head called with path: {path}, lines: {lines}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist"
        if not os.path.isfile(path):
            return f"Error: '{path}' is not a file"
        
        with open(path, 'r', encoding='utf-8') as f:
            result = ''.join(f.readline() for _ in range(lines))
            
        return result
    except Exception as e:
        print(f"[ERROR] head failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Display the last part of files.")
async def tail(path: str, lines: int = 10) -> Dict[str, Any]:
    try:
        print(f"[DEBUG] tail called with path: {path}, lines: {lines}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"File '{path}' does not exist"}
        if not os.path.isfile(path):
            return {"error": f"'{path}' is not a file"}
        cmd = ["tail", "-n", str(lines), path]
        result = await run_command(cmd)
        return result
    except Exception as e:
        print(f"[ERROR] tail failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Print the resolved path of a symbolic link.")
def readlink(path: str) -> str:
    """Print the resolved path of a symbolic link."""
    try:
        print(f"[DEBUG] readlink called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist"
        if not os.path.islink(path):
            return f"Error: '{path}' is not a symbolic link"
        
        return os.readlink(path)
    except Exception as e:
        print(f"[ERROR] readlink failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Print the resolved absolute path.")
def realpath(path: str) -> str:
    """Print the resolved absolute path."""
    try:
        print(f"[DEBUG] realpath called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: Path '{path}' does not exist"
        
        return os.path.realpath(path)
    except Exception as e:
        print(f"[ERROR] realpath failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

# ===== TEXT MANIPULATION TOOLS =====

@mcp.tool(description="Select specific columns from each line.")
async def cut(path: str, delimiter: str = '\t', fields: str = '1') -> Dict[str, Any]:
    try:
        print(f"[DEBUG] cut called with path: {path}, delimiter: {delimiter}, fields: {fields}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"File '{path}' does not exist"}
        if not os.path.isfile(path):
            return {"error": f"'{path}' is not a file"}
        cmd = ["cut", f"-d{delimiter}", f"-f{fields}", path]
        result = await run_command(cmd)
        return result
    except Exception as e:
        print(f"[ERROR] cut failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Sort lines of text files.")
async def sort(path: str, reverse: bool = False, numeric: bool = False, field: Optional[int] = None) -> Dict[str, Any]:
    try:
        print(f"[DEBUG] sort called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"File '{path}' does not exist"}
        if not os.path.isfile(path):
            return {"error": f"'{path}' is not a file"}
        cmd = ["sort"]
        if reverse:
            cmd.append("-r")
        if numeric:
            cmd.append("-n")
        if field is not None:
            cmd.append(f"-k{field}")
        cmd.append(path)
        result = await run_command(cmd)
        return result
    except Exception as e:
        print(f"[ERROR] sort failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Report or filter out repeated lines.")
async def uniq(path: str, count: bool = False, repeated: bool = False, ignore_case: bool = False) -> Dict[str, Any]:
    try:
        print(f"[DEBUG] uniq called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"File '{path}' does not exist"}
        if not os.path.isfile(path):
            return {"error": f"'{path}' is not a file"}
        cmd = ["uniq"]
        if count:
            cmd.append("-c")
        if repeated:
            cmd.append("-d")
        if ignore_case:
            cmd.append("-i")
        cmd.append(path)
        result = await run_command(cmd)
        return result
    except Exception as e:
        print(f"[ERROR] uniq failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Print line, word, and byte counts.")
def wc(path: str, lines: bool = True, words: bool = True, bytes: bool = True) -> Dict[str, Any]:
    """Print line, word, and byte counts."""
    try:
        print(f"[DEBUG] wc called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"File '{path}' does not exist"}
        if not os.path.isfile(path):
            return {"error": f"'{path}' is not a file"}
        
        result = {}
        
        # Count lines if requested
        if lines:
            with open(path, 'r', encoding='utf-8') as f:
                result["lines"] = sum(1 for _ in f)
        
        # Count words if requested
        if words:
            with open(path, 'r', encoding='utf-8') as f:
                result["words"] = sum(len(line.split()) for line in f)
        
        # Count bytes if requested
        if bytes:
            result["bytes"] = os.path.getsize(path)
            
        return result
    except Exception as e:
        print(f"[ERROR] wc failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Number lines in a file.")
def nl(path: str, number_empty: bool = True, number_format: str = '%6d  ') -> str:
    """Number lines in a file."""
    try:
        print(f"[DEBUG] nl called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist"
        if not os.path.isfile(path):
            return f"Error: '{path}' is not a file"
        
        # Number lines
        result = []
        with open(path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if number_empty or line.strip():
                    result.append(number_format % i + line)
                else:
                    result.append(line)
        
        return ''.join(result)
    except Exception as e:
        print(f"[ERROR] nl failed: {str(e)}", file=sys.stderr, flush=True)
        return f"Error: {str(e)}"

@mcp.tool(description="Split a file into smaller parts.")
async def split(path: str, prefix: str = 'x', lines: Optional[int] = 1000, bytes_size: Optional[str] = None) -> Dict[str, Any]:
    try:
        print(f"[DEBUG] split called with path: {path}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"File '{path}' does not exist"}
        if not os.path.isfile(path):
            return {"error": f"'{path}' is not a file"}
        cmd = ["split"]
        if lines is not None:
            cmd.extend(["-l", str(lines)])
        if bytes_size is not None:
            cmd.extend(["-b", bytes_size])
        cmd.extend([path, prefix])
        result = await run_command(cmd)
        files = glob.glob(f"{prefix}*")
        return {"success": True, "parts": len(files), "files": files, **result}
    except Exception as e:
        print(f"[ERROR] split failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

# ===== ARCHIVE & COMPRESSION TOOLS =====

@mcp.tool(description="Create, extract, or list tar archives.")
async def tar(operation: str, archive_file: str, files: Optional[List[str]] = None, options: str = "") -> Dict[str, Any]:
    try:
        print(f"[DEBUG] tar called with operation: {operation}, archive: {archive_file}", file=sys.stderr, flush=True)
        op_flags = {"create": "c", "extract": "x", "list": "t"}
        if operation not in op_flags:
            return {"error": f"Invalid operation '{operation}'. Use 'create', 'extract', or 'list'."}
        flag = op_flags[operation]
        cmd = ["tar", f"-{flag}vf"]
        if archive_file.endswith('.gz') or archive_file.endswith('.tgz'):
            cmd[1] += 'z'
        elif archive_file.endswith('.bz2'):
            cmd[1] += 'j'
        elif archive_file.endswith('.xz'):
            cmd[1] += 'J'
        if options:
            cmd.extend(options.split())
        cmd.append(archive_file)
        if operation == "create" and files:
            cmd.extend(files)
        result = await run_command(cmd)
        return result
    except Exception as e:
        print(f"[ERROR] tar failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Compress or decompress files.")
async def gzip(path: str, decompress: bool = False, keep: bool = False) -> Dict[str, Any]:
    try:
        print(f"[DEBUG] gzip called with path: {path}, decompress: {decompress}", file=sys.stderr, flush=True)
        if not os.path.exists(path):
            return {"error": f"Path '{path}' does not exist"}
        cmd = ["gzip"]
        if decompress:
            cmd.append("-d")
        if keep:
            cmd.append("-k")
        cmd.append(path)
        result = await run_command(cmd)
        return result
    except Exception as e:
        print(f"[ERROR] gzip failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

@mcp.tool(description="Create or extract zip archives.")
async def zip(operation: str, archive_file: str, files: Optional[List[str]] = None, options: str = "") -> Dict[str, Any]:
    try:
        print(f"[DEBUG] zip called with operation: {operation}, archive: {archive_file}", file=sys.stderr, flush=True)
        if operation not in ["create", "extract"]:
            return {"error": f"Invalid operation '{operation}'. Use 'create' or 'extract'."}
        if operation == "create":
            if not files:
                return {"error": "No files specified for zip creation"}
            cmd = ["zip"]
            if options:
                cmd.extend(options.split())
            cmd.append(archive_file)
            cmd.extend(files)
            result = await run_command(cmd)
            return result
        else:
            if not os.path.exists(archive_file):
                return {"error": f"Archive '{archive_file}' does not exist"}
            cmd = ["unzip"]
            if options:
                cmd.extend(options.split())
            cmd.append(archive_file)
            result = await run_command(cmd)
            return result
    except Exception as e:
        print(f"[ERROR] zip failed: {str(e)}", file=sys.stderr, flush=True)
        return {"error": str(e)}

# ===== TOOLS FOR WORKING WITH PDF =====

@mcp.tool(description="Creates a new PDF document from the given text.")
async def tool_create_pdf(file_path: str, text_content: str, title: str = "Document", author: str = "AI Agent") -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_create_pdf for file '{file_path}'", file=sys.stderr)
    return await create_pdf_from_text(file_path, text_content, title, author)

@mcp.tool(description="Merges several PDF files into one.")
async def tool_merge_pdfs(output_path: str, input_paths: List[str]) -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_merge_pdfs for output '{output_path}'", file=sys.stderr)
    # Use * to unpack the list into arguments
    return await merge_pdfs(output_path, *input_paths)

@mcp.tool(description="Extracts specified pages from a PDF file.")
async def tool_extract_pdf_pages(input_path: str, output_path: str, pages_to_extract: List[int]) -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_extract_pdf_pages from '{input_path}'", file=sys.stderr)
    return await extract_pdf_pages(input_path, output_path, pages_to_extract)

# ===== TOOLS FOR WORKING WITH WORD (DOCX) =====

@mcp.tool(description="Creates a new Word document (.docx).")
async def tool_create_docx(file_path: str, content: str = "") -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_create_docx for file '{file_path}'", file=sys.stderr)
    return await create_docx(file_path, content)

@mcp.tool(description="Adds a new paragraph to a DOCX document.")
async def tool_add_text_to_docx(file_path: str, text_to_add: str) -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_add_text_to_docx for file '{file_path}'", file=sys.stderr)
    return await add_text_to_docx(file_path, text_to_add)

@mcp.tool(description="Replaces text in a DOCX document.")
async def tool_replace_text_in_docx(file_path: str, old_text: str, new_text: str) -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_replace_text_in_docx for file '{file_path}'", file=sys.stderr)
    return await replace_text_in_docx(file_path, old_text, new_text)

# ===== TOOLS FOR WORKING WITH POWERPOINT (PPTX) =====

@mcp.tool(description="Creates a new PowerPoint presentation (.pptx).")
async def tool_create_pptx(file_path: str, title: str = "", subtitle: str = "") -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_create_pptx for file '{file_path}'", file=sys.stderr)
    return await create_pptx(file_path, title, subtitle)

@mcp.tool(description="Adds a new slide to a PPTX presentation.")
async def tool_add_slide_to_pptx(file_path: str, layout_index: int = 1, title: str = "", content: str = "") -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_add_slide_to_pptx for file '{file_path}'", file=sys.stderr)
    return await add_slide_to_pptx(file_path, layout_index, title, content)

# ===== TOOLS FOR WORKING WITH EXCEL (XLSX) =====

@mcp.tool(description="Creates a new Excel document (.xlsx).")
async def tool_create_xlsx(file_path: str, sheet_name: str = "Sheet1") -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_create_xlsx for file '{file_path}'", file=sys.stderr)
    return await create_xlsx(file_path, sheet_name)

@mcp.tool(description="Writes a value to an Excel cell.")
async def tool_write_to_excel_cell(file_path: str, sheet_name: str, cell_address: str, value: Any) -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_write_to_excel_cell to cell {cell_address}", file=sys.stderr)
    return await write_to_excel_cell(file_path, sheet_name, cell_address, value)

@mcp.tool(description="Reads a value from an Excel cell.")
async def tool_read_from_excel_cell(file_path: str, sheet_name: str, cell_address: str) -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_read_from_excel_cell from cell {cell_address}", file=sys.stderr)
    return await read_from_excel_cell(file_path, sheet_name, cell_address)

@mcp.tool(description="Writes a 2D array of data to a range of Excel cells.")
async def tool_write_data_to_excel_range(file_path: str, sheet_name: str, start_cell: str, data: List[List[Any]]) -> Dict[str, Any]:
    print(f"[TOOL] Called: tool_write_data_to_excel_range starting from {start_cell}", file=sys.stderr)
    return await write_data_to_excel_range(file_path, sheet_name, start_cell, data)

