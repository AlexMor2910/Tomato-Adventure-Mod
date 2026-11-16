// Bounded static analysis only; modifies the disposable Ghidra database, never ROM bytes.
// @category TomatoAdventure
import ghidra.app.script.GhidraScript;
import ghidra.app.cmd.disassemble.DisassembleCommand;
import ghidra.program.model.address.*;
import ghidra.program.model.listing.*;
import java.io.*;
import java.math.BigInteger;

public class TraceGimmickLoader extends GhidraScript {
	private Address a(long v) { return toAddr(v); }
	private void thumb(long start, long end) throws Exception {
		AddressSet range = new AddressSet(a(start), a(end));
		// Seed only the entry. Thumb flow propagates context; do not overwrite
		// context on previously decoded branch destinations in overlapping windows.
		if (getInstructionAt(a(start)) == null)
			currentProgram.getProgramContext().setValue(currentProgram.getRegister("TMode"), a(start), a(start), BigInteger.ONE);
		else if (!BigInteger.ONE.equals(currentProgram.getProgramContext().getValue(currentProgram.getRegister("TMode"), a(start), false)))
			throw new IllegalStateException("Existing execution-mode conflict at "+a(start));
		DisassembleCommand cmd = new DisassembleCommand(a(start), range, true);
		if (!cmd.applyTo(currentProgram, monitor)) println("DISASSEMBLY WARNING " + cmd.getStatusMsg());
	}
	public void run() throws Exception {
		String[] args = getScriptArgs();
		currentProgram.getMemory().createUninitializedBlock("IWRAM", a(0x03000000L), 0x8000, false);
		try (PrintWriter out = new PrintWriter(new File(args[0]), "UTF-8")) {
			out.println("Language: " + currentProgram.getLanguageID());
			out.println("Image base: " + currentProgram.getImageBase());
			for (ghidra.program.model.mem.MemoryBlock block:currentProgram.getMemory().getBlocks())
				out.println("Memory block: "+block.getName()+" "+block.getStart()+".."+block.getEnd()+" initialized="+block.isInitialized());
			// Entry/prologue, coherent Thumb control flow, and source patch corroborate TMode=1.
			thumb(0x08065518L, 0x080655D3L);
			thumb(0x080655E4L, 0x080656C1L);
			int loaderCount=0;
			for (long[] span : new long[][]{{0x08065518L,0x080655D4L},{0x080655E4L,0x080656C2L}}) {
				long p=span[0];
				while (p<span[1]) {
					Instruction ins=getInstructionAt(a(p));
					if (ins==null || p+ins.getLength()>span[1]) throw new IllegalStateException("Loader coverage gap at "+a(p));
					p+=ins.getLength(); loaderCount++;
				}
			}
			out.println("Loader instruction count: "+loaderCount);
			AddressSet body = new AddressSet(a(0x08065518L), a(0x080655D3L));
			body.add(a(0x080655E4L), a(0x080656C1L));
			currentProgram.getFunctionManager().createFunction(null, a(0x08065518L), body, ghidra.program.model.symbol.SourceType.ANALYSIS);
			out.println("\nLOADER (literal pool 080655d4..080655e3 excluded)");
			InstructionIterator it = currentProgram.getListing().getInstructions(body, true);
			while (it.hasNext()) {
				Instruction ins = it.next(); out.println(ins.getAddress() + "  " + ins);
				for (ghidra.program.model.symbol.Reference ref : ins.getReferencesFrom())
					out.println("  REF " + ref.getReferenceType() + " " + ref.getToAddress());
			}
			out.println("\nLITERAL WORDS");
			for (long p : new long[]{0x080655D4L,0x080655D8L,0x080655DCL,0x080655E0L,0x080656C4L,0x080656C8L,0x080656CCL,0x080656D0L,0x080656D4L,0x080656D8L})
				out.printf("%08x = %08x%n", p, getInt(a(p)));
			// Scan raw bytes for potential Thumb BL callers; matches are candidates until context validated.
			out.println("\nRAW THUMB BL CANDIDATES (not an exhaustive ARM/indirect caller graph)");
			for (long p=0x08000000L; p<0x087ffffcL; p+=2) {
				int h=getShort(a(p)) & 65535, l=getShort(a(p+2)) & 65535;
				if ((h & 0xf800)!=0xf000 || (l & 0xf800)!=0xf800) continue;
				int delta=((h & 2047)<<12)|((l & 2047)<<1);
				if ((delta & 0x400000)!=0) delta|=~0x7fffff;
				if (p+4+delta==0x08065518L) out.printf("%08x%n",p);
			}
			out.println("\nALIGNED RAW WORD MATCHES (data candidates, not code xrefs)");
			for (long p=0x08000000L;p<0x08800000L;p+=4) {
				long v=Integer.toUnsignedLong(getInt(a(p)));
				if (v==0x03003F34L || v==0x0862C250L || v==0x0862C1F8L || v==0x08065519L)
					out.printf("%08x = %08x%n",p,v);
			}
			// Follow-up seeds: direct BL caller, source-known text consumer, and
			// table-literal getter/scaler entries corroborated by local control flow.
			long[][] windows = {
				{0x0806ACA0L,0x0806AD4BL}, {0x0802B7F0L,0x0802B8BFL},
				{0x080754B0L,0x080754D3L}, {0x08075970L,0x080759CFL},
				{0x08075AA4L,0x08075AB1L}, {0x08075AB2L,0x08075AEDL}, {0x08075304L,0x08075311L},
				{0x080755C6L,0x080755D3L}, {0x080F7B08L,0x080F7B9DL},
				{0x0807565CL,0x080756BFL}
			};
			for (int i=0;i<9;i++) {
				long st=0x08075A04L+i*0x14L;
				thumb(st,st+0x0d);
			}
			for (long[] w : windows) thumb(w[0],w[1]);
			createFunction(a(0x0806ACA0L), null);
			createFunction(a(0x080754B0L), null);
			createFunction(a(0x080F7B08L), null);
			out.println("\nTARGETED CONTEXTS (some are basic blocks, not complete functions)");
			for (long[] w : windows) dump(out, new AddressSet(a(w[0]),a(w[1])));
			for (int i=0;i<9;i++) {
				long st=0x08075A04L+i*0x14L;
				dump(out,new AddressSet(a(st),a(st+0x0d)));
			}
			out.println("\nSCALER SWITCH TARGET WORDS (data, not instructions)");
			for (long p=0x080759E0L;p<0x08075A04L;p+=4) out.printf("%08x = %08x%n",p,getInt(a(p)));
			out.println("\nPOINTER TAIL TARGETS (50 original records; no target assets exported)");
			for (int id=1;id<=50;id++) {
				for (int off=0x3c;off<0x58;off+=4) {
					long p=0x0862C250L+(id-1)*0x58+off;
					out.printf("id=%02x field=+%02x slot=%08x value=%08x%n",id,off,p,getInt(a(p)));
				}
			}
			out.println("TRACE_COMPLETE");
		}
	}
	private void dump(PrintWriter out, AddressSet set) {
		out.println("BLOCK " + set.getMinAddress() + ".." + set.getMaxAddress());
		InstructionIterator it = currentProgram.getListing().getInstructions(set,true);
		while (it.hasNext()) {
			Instruction ins=it.next(); out.println(ins.getAddress()+"  "+ins);
			for (ghidra.program.model.symbol.Reference ref : ins.getReferencesFrom()) {
				out.print("  REF "+ref.getReferenceType()+" "+ref.getToAddress());
				try { if (ref.getReferenceType().isRead() && ins.getMnemonicString().equals("ldr")) out.printf(" literal=%08x", getInt(ref.getToAddress())); } catch (Exception ignored) { }
				out.println();
			}
		}
	}
}
