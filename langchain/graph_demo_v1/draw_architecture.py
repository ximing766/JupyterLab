from graphviz import Digraph
import os

def draw():
    dot = Digraph(comment='LangGraph Agent Architecture', format='png')
    dot.attr(rankdir='TB', size='12,16', dpi='150', bgcolor='white')
    dot.attr('graph', fontname='Helvetica', fontsize='13', pad='0.5', splines='polyline')
    dot.attr('node', fontname='Helvetica', fontsize='12')
    dot.attr('edge', fontname='Helvetica', fontsize='11')

    # ── Entry / Exit ──────────────────────────────────────────────────────────
    dot.node('START', 'START', shape='circle', style='filled',
             fillcolor='#2d6a4f', fontcolor='white', color='#1b4332', width='0.8')
    dot.node('END', 'END', shape='doublecircle', style='filled',
             fillcolor='#6c757d', fontcolor='white', color='#495057', width='0.8')

    # ── User / main.py ────────────────────────────────────────────────────────
    with dot.subgraph(name='cluster_entry') as c:
        c.attr(label='main.py  —  Entry Point', style='filled',
               fillcolor='#f0f4ff', color='#7b9cda', fontname='Helvetica', fontsize='12')
        c.node('user_input', 'User Input\n(REPL / single-shot)', shape='parallelogram',
               style='filled', fillcolor='#dbe4ff', color='#4c6ef5')
        c.node('streaming', 'run_streaming()\nstream_mode="messages"\nfilter AIMessageChunk',
               shape='box', style='filled,rounded', fillcolor='#dbe4ff', color='#4c6ef5')

    # ── State ─────────────────────────────────────────────────────────────────
    with dot.subgraph(name='cluster_state') as c:
        c.attr(label='state.py  —  AgentState', style='filled',
               fillcolor='#fff9db', color='#f59f00', fontname='Helvetica', fontsize='12')
        c.node('state', 'AgentState\n─────────────\nmessages: list[AnyMessage]\n(add_messages reducer)',
               shape='record', style='filled', fillcolor='#fff3bf', color='#e67700')

    # ── Graph (LangGraph) ─────────────────────────────────────────────────────
    with dot.subgraph(name='cluster_graph') as c:
        c.attr(label='graph.py  —  StateGraph', style='filled',
               fillcolor='#f3f0ff', color='#9775fa', fontname='Helvetica', fontsize='12')
        c.node('checkpointer', 'InMemorySaver\n(per thread_id)', shape='cylinder',
               style='filled', fillcolor='#e5dbff', color='#7048e8')

        # ── Nodes ─────────────────────────────────────────────────────────────
        with c.subgraph(name='cluster_nodes') as n:
            n.attr(label='Nodes  (nodes.py)', style='dashed', color='#9775fa',
                   fontname='Helvetica', fontsize='11')
            n.node('model_node',
                   'model_node\n─────────────\nSystemMessage + history\n→ LLM (DeepSeek-V3)\n← AIMessage / tool_calls',
                   shape='box', style='filled,rounded', fillcolor='#d0bfff', color='#5f3dc4')
            n.node('tool_node',
                   'tool_node\n(ToolNode prebuilt)\n─────────────\ndispatch tool_calls\n→ ToolMessage',
                   shape='box', style='filled,rounded', fillcolor='#d0bfff', color='#5f3dc4')

        # ── Router ────────────────────────────────────────────────────────────
        c.node('router', 'should_continue()\n─────────────\ntool_calls? → "tools"\nelse → "end"',
               shape='diamond', style='filled', fillcolor='#ffe8cc', color='#d9480f')

    # ── LLM / Config ─────────────────────────────────────────────────────────
    with dot.subgraph(name='cluster_llm') as c:
        c.attr(label='config.py  —  ByteDance Ark API', style='filled',
               fillcolor='#e6fcf5', color='#20c997', fontname='Helvetica', fontsize='12')
        c.node('llm', 'ChatOpenAI (streaming)\n─────────────\nmodel: deepseek-v3-2-251201\nbase_url: ark.cn-beijing\ntemp=0.5  max_tokens=25000',
               shape='box', style='filled,rounded', fillcolor='#c3fae8', color='#0ca678')

    # ── Tools ─────────────────────────────────────────────────────────────────
    with dot.subgraph(name='cluster_tools') as c:
        c.attr(label='tools.py  —  ALL_TOOLS', style='filled',
               fillcolor='#fff0f6', color='#f06595', fontname='Helvetica', fontsize='12')
        c.node('t1', 'get_current_datetime\n(Beijing time)', shape='box',
               style='filled,rounded', fillcolor='#fcc2d7', color='#c2255c')
        c.node('t2', 'fetch_text_from_url\n(HTTP GET)', shape='box',
               style='filled,rounded', fillcolor='#fcc2d7', color='#c2255c')
        c.node('t3', 'calculate\n(safe eval)', shape='box',
               style='filled,rounded', fillcolor='#fcc2d7', color='#c2255c')

    # ── Edges ─────────────────────────────────────────────────────────────────
    dot.edge('START', 'user_input')
    dot.edge('user_input', 'streaming', label='HumanMessage')
    dot.edge('streaming', 'model_node', label='invoke / stream')
    dot.edge('model_node', 'llm', label='bind_tools\n+ invoke', style='dashed', color='#20c997')
    dot.edge('llm', 'model_node', style='dashed', color='#20c997')
    dot.edge('model_node', 'router')
    dot.edge('router', 'tool_node', label='"tools"', color='#d9480f')
    dot.edge('router', 'END', label='"end"', color='#6c757d')
    dot.edge('tool_node', 'model_node', label='ToolMessage\n(loop back)')
    dot.edge('tool_node', 't1', style='dashed', color='#f06595')
    dot.edge('tool_node', 't2', style='dashed', color='#f06595')
    dot.edge('tool_node', 't3', style='dashed', color='#f06595')
    dot.edge('model_node', 'state', label='read/write', style='dotted', color='#e67700')
    dot.edge('checkpointer', 'state', label='persist', style='dotted', color='#7048e8')
    dot.edge('streaming', 'END', label='stream tokens\nto stdout', style='dashed', color='#4c6ef5')

    try:
        output = dot.render('graph_demo_v1_architecture', directory='.', cleanup=True)
        print(f"Generated: {os.path.abspath(output)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    draw()
