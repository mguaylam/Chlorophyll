// Ghidra headless script (Java). Find functions referencing strings that match
// given keywords, decompile them to pseudo-C.
// Args: space-separated keywords.
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.*;
import ghidra.program.model.listing.*;
import ghidra.program.model.symbol.*;
import ghidra.program.model.address.Address;
import ghidra.util.task.ConsoleTaskMonitor;
import java.util.*;

public class XrefDecompile extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        List<String> keywords = new ArrayList<>();
        if (args != null && args.length > 0) for (String a : args) keywords.add(a);
        else { keywords.add("S12"); keywords.add("EvAcApp"); }
        println("=== keywords: " + keywords + " ===");

        Listing listing = currentProgram.getListing();
        FunctionManager fm = currentProgram.getFunctionManager();
        ReferenceManager refmgr = currentProgram.getReferenceManager();

        // 1) defined strings containing a keyword
        Map<Address,String[]> strHits = new HashMap<>();
        DataIterator dit = listing.getDefinedData(true);
        while (dit.hasNext()) {
            Data d = dit.next();
            Object v = null;
            try { v = d.getValue(); } catch (Exception e) {}
            if (v == null) continue;
            String s = v.toString();
            for (String kw : keywords) {
                if (s.contains(kw)) { strHits.put(d.getAddress(), new String[]{s, kw}); break; }
            }
        }
        println("strings matched: " + strHits.size());

        // 2) walk refs back to a containing function (max 2 hops via literal pool)
        Map<Function,Set<String>> targets = new LinkedHashMap<>();
        for (Map.Entry<Address,String[]> e : strHits.entrySet()) {
            String kw = e.getValue()[1];
            String text = e.getValue()[0];
            String tag = "[" + kw + "] " + (text.length() > 60 ? text.substring(0,60) : text);
            Set<Address> seen = new HashSet<>();
            Deque<Address> stack = new ArrayDeque<>();
            stack.push(e.getKey());
            while (!stack.isEmpty()) {
                Address a = stack.pop();
                if (!seen.add(a)) continue;
                for (Reference r : refmgr.getReferencesTo(a)) {
                    Address fa = r.getFromAddress();
                    Function f = fm.getFunctionContaining(fa);
                    if (f != null) targets.computeIfAbsent(f, k -> new TreeSet<>()).add(tag);
                    else stack.push(fa);
                }
            }
        }
        println("functions to decompile: " + targets.size());

        // 3) decompile
        DecompInterface dec = new DecompInterface();
        dec.openProgram(currentProgram);
        ConsoleTaskMonitor mon = new ConsoleTaskMonitor();
        List<Function> funcs = new ArrayList<>(targets.keySet());
        funcs.sort(Comparator.comparingLong(f -> f.getEntryPoint().getOffset()));
        for (Function f : funcs) {
            println("\n==============================================================================");
            println("FUNCTION " + f.getName() + " @ " + f.getEntryPoint());
            println("references strings:");
            for (String t : targets.get(f)) println("   " + t);
            println("------------------------------------------------------------------------------");
            DecompileResults res = dec.decompileFunction(f, 60, mon);
            if (res != null && res.decompileCompleted())
                println(res.getDecompiledFunction().getC());
            else
                println("// decompilation failed: " + (res != null ? res.getErrorMessage() : "no result"));
        }
    }
}
