// Ghidra headless script (Java). Decompile the function(s) containing the given
// hex addresses (or the function at that entry). Args: space-separated hex addrs.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.app.cmd.disassemble.ArmDisassembleCommand;
import ghidra.app.cmd.function.CreateFunctionCmd;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.Address;
import ghidra.program.model.mem.Memory;
import ghidra.util.task.ConsoleTaskMonitor;

public class DecompAt extends GhidraScript {
    // Result of a prologue search: address + whether it is Thumb.
    private Address proAddr; private boolean proThumb;

    // Scan backward from `from` for a function prologue. Detects ARM
    // STMFD sp!,{...,lr} (E92D4xxx) and Thumb PUSH {...,LR} (0xB5xx). Sets
    // proAddr/proThumb; returns proAddr (or null).
    private Address findPrologue(Address from, int maxBack) throws Exception {
        Memory mem = currentProgram.getMemory();
        long base = from.getOffset() & ~1L;
        for (long o = base; o >= base - maxBack; o -= 2) {
            Address a = from.getNewAddress(o);
            try {
                // Thumb PUSH {...,LR}: halfword 0xB5xx (byte[o+1]==0xB5)
                int hw = mem.getShort(a) & 0xffff;
                if ((hw & 0xFF00) == 0xB500) { proAddr = a; proThumb = true; return a; }
                // ARM STMFD sp!,{...,lr} on 4-aligned addrs
                if ((o & 3) == 0) {
                    int w = mem.getInt(a);
                    int b3 = (w >> 24) & 0xff, b2 = (w >> 16) & 0xff;
                    if (b3 == 0xE9 && b2 == 0x2D && ((w >> 14) & 1) == 1) {
                        proAddr = a; proThumb = false; return a;
                    }
                }
            } catch (Exception e) { break; }
        }
        return null;
    }

    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        FunctionManager fm = currentProgram.getFunctionManager();
        DecompInterface dec = new DecompInterface();
        dec.openProgram(currentProgram);
        ConsoleTaskMonitor mon = new ConsoleTaskMonitor();
        for (String a : args) {
            long off = Long.parseLong(a.replace("0x", ""), 16);
            Address addr = currentProgram.getAddressFactory().getDefaultAddressSpace().getAddress(off);
            Function f = fm.getFunctionContaining(addr);
            println("\n==============================================================================");
            if (f == null) {
                Address start = findPrologue(addr, 0x2000);
                if (start == null) {
                    println("// no function contains " + addr + " and no ARM prologue found within 0x2000");
                    continue;
                }
                println("// no function at " + addr + "; found " + (proThumb ? "Thumb" : "ARM")
                        + " prologue at " + start + ", disassembling");
                new ArmDisassembleCommand(start, null, proThumb).applyTo(currentProgram, mon);
                CreateFunctionCmd cfc = new CreateFunctionCmd(start);
                cfc.applyTo(currentProgram, mon);
                f = fm.getFunctionContaining(start);
                if (f == null) { println("// could not create a function at " + start); continue; }
            }
            println("FUNCTION " + f.getName() + " @ " + f.getEntryPoint() + " (for addr " + addr + ")");
            println("------------------------------------------------------------------------------");
            DecompileResults res = dec.decompileFunction(f, 60, mon);
            if (res != null && res.decompileCompleted())
                println(res.getDecompiledFunction().getC());
            else
                println("// decompilation failed: " + (res != null ? res.getErrorMessage() : "no result"));
        }
    }
}
