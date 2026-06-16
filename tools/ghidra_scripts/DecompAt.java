// Ghidra headless script (Java). Decompile the function(s) containing the given
// hex addresses (or the function at that entry). Args: space-separated hex addrs.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.address.Address;
import ghidra.util.task.ConsoleTaskMonitor;

public class DecompAt extends GhidraScript {
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
                println("// no function contains " + addr + " — disassembling nearby instead");
                continue;
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
