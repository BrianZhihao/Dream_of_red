import streamlit as st
import pandas as pd
from streamlit_agraph import agraph, Node, Edge, Config
import os

# 设置页面
st.set_page_config(
    page_title="人物关系图谱",
    page_icon="🕸️",
    layout="wide"
)

st.title("🕸️ 人物关系图谱")

# 文件路径配置
NODES_FILE = "nodes.csv"  # 节点文件路径
EDGES_FILE = "edges.csv"  # 边文件路径

@st.cache_data
def load_data():
    """从本地文件加载数据"""
    
    # 检查文件是否存在
    if not os.path.exists(NODES_FILE):
        st.error(f"节点文件 {NODES_FILE} 不存在")
        return None, None
    
    if not os.path.exists(EDGES_FILE):
        st.error(f"边文件 {EDGES_FILE} 不存在")
        return None, None
    
    try:
        # 读取节点数据
        nodes_df = pd.read_csv(NODES_FILE)
        st.success(f"成功加载节点数据: {len(nodes_df)} 个节点")
        
        # 读取边数据
        edges_df = pd.read_csv(EDGES_FILE)
        st.success(f"成功加载关系数据: {len(edges_df)} 条关系")
        
        return nodes_df, edges_df
        
    except Exception as e:
        st.error(f"读取文件时出错: {e}")
        return None, None

# 加载数据
nodes_df, edges_df = load_data()

if nodes_df is not None and edges_df is not None:
    # 显示原始数据结构
    with st.expander("查看数据结构"):
        col1, col2 = st.columns(2)
        with col1:
            st.write("节点数据:")
            st.dataframe(nodes_df.head())
        with col2:
            st.write("边数据:")
            st.dataframe(edges_df.head())

    # 侧边栏配置
    with st.sidebar:
        st.header("图谱配置")
        
        # 布局设置
        layout = st.selectbox(
            "选择布局算法",
            ["force", "hierarchy", "circular"],
            help="force: 力导向布局 | hierarchy: 层次布局 | circular: 环形布局"
        )
        
        base_node_size = st.slider("基础节点大小", 10, 30, 20)
        show_labels = st.checkbox("显示节点标签", value=True)
        
        st.divider()
        st.subheader("权重设置")
        
        # 根据Weight调整节点大小
        use_weight_size = st.checkbox("根据权重调整节点大小", value=False)
        weight_multiplier = st.slider("权重放大倍数", 1, 10, 3)
        
        # 根据Weight调整边粗细
        use_weight_edge = st.checkbox("根据权重调整边粗细", value=True)
        edge_weight_multiplier = st.slider("边权重倍数", 0.5, 5.0, 1.5)
        
        st.divider()
        st.subheader("模块筛选")
        
        # 检查module列是否存在
        if 'module' in nodes_df.columns:
            all_modules = ['所有模块'] + list(nodes_df['module'].unique())
            selected_module = st.selectbox("筛选模块", all_modules)
        else:
            st.info("节点文件中没有'module'列")
            selected_module = '所有模块'

    # 构建节点和边对象
    nodes = []
    edges = []

    # 模块颜色映射（如果module列存在）
    module_colors = {}
    if 'module' in nodes_df.columns:
        unique_modules = nodes_df['module'].unique()
        color_palette = [
            '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#F7DC6F',
            '#BB8FCE', '#85C1E9', '#F8C471', '#82E0AA', '#F1948A'
        ]
        for i, module in enumerate(unique_modules):
            module_colors[module] = color_palette[i % len(color_palette)]
    else:
        # 如果没有module列，所有节点用同一颜色
        default_color = '#1F77B4'

    # 处理节点数据
    node_dict = {}  # 用于存储节点信息
    node_ids = set()  # 用于快速检查节点是否存在
    
    for _, row in nodes_df.iterrows():
        # 使用实际的列名
        node_id = str(row['id'])
        
        # 节点标签
        node_label = str(row['label']) if pd.notna(row['label']) else node_id
        
        # 节点模块（如果存在）
        node_module = str(row['module']) if 'module' in nodes_df.columns and pd.notna(row['module']) else '默认'
        
        # 模块筛选（如果module列存在）
        if 'module' in nodes_df.columns and selected_module != '所有模块' and node_module != selected_module:
            continue
        
        # 节点大小（基于权重，如果weight列存在）
        if use_weight_size and 'weight' in nodes_df.columns and pd.notna(row.get('weight')):
            try:
                weight = float(row['weight'])
                node_size = base_node_size + (weight * weight_multiplier)
            except:
                node_size = base_node_size
        else:
            node_size = base_node_size
        
        # 节点颜色
        if 'module' in nodes_df.columns:
            color = module_colors.get(node_module, '#1F77B4')
        else:
            color = '#1F77B4'
        
        node = Node(
            id=node_id,
            label=node_label if show_labels else "",
            size=node_size,
            color=color,
            # 修改这里：将字体颜色改为黑色
            font={"color": "black", "size": 12, "strokeColor": "white", "strokeWidth": 2},  # 添加白色描边让黑色文字更清晰
            shape="dot"
        )
        nodes.append(node)
        node_ids.add(node_id)  # 添加到节点ID集合
        node_dict[node_id] = {
            'module': node_module, 
            'label': node_label,
            'size': node_size
        }

    # 处理边数据
    for _, row in edges_df.iterrows():
        # 源节点和目标节点
        source = str(row['source'])
        target = str(row['target'])
        
        # 检查两个节点是否都存在
        source_exists = source in node_ids
        target_exists = target in node_ids
        
        if not source_exists or not target_exists:
            continue
        
        # 边权重
        if use_weight_edge and 'weight' in edges_df.columns and pd.notna(row['weight']):
            try:
                weight = float(row['weight'])
                edge_width = max(1, min(5, weight * edge_weight_multiplier))
            except:
                edge_width = 2
        else:
            edge_width = 2
        
        # 边的颜色
        if 'module' in nodes_df.columns:
            source_module = node_dict.get(source, {}).get('module', '默认')
            edge_color = module_colors.get(source_module, '#666666')
        else:
            edge_color = '#666666'
        
        edge = Edge(
            source=source,
            target=target,
            label="",
            color=edge_color,
            width=edge_width
        )
        edges.append(edge)

    # 配置图表
    if layout == "hierarchy":
        config = Config(
            width=1000,
            height=700,
            directed=False,
            physics=True,
            hierarchical=True,
            **{
                "physics": {
                    "enabled": True,
                    "stabilization": {"iterations": 100}
                }
            }
        )
    else:
        config = Config(
            width=1000,
            height=700,
            directed=False,
            physics=True,
            hierarchical=False
        )

    # 显示图表
    st.subheader("交互式关系图谱")
    
    if not nodes:
        st.warning("没有找到符合筛选条件的节点")
    elif not edges:
        st.warning("没有找到符合筛选条件的关系")
    else:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            try:
                return_value = agraph(nodes=nodes, edges=edges, config=config)
                if return_value:
                    selected_node_info = node_dict.get(return_value, {})
                    st.info(f"**选中的节点:** {return_value}")
                    st.write(f"**标签:** {selected_node_info.get('label', '未知')}")
                    if 'module' in nodes_df.columns:
                        st.write(f"**模块:** {selected_node_info.get('module', '未知')}")
                    
                    # 显示与该节点相关的边
                    related_edges = [
                        edge for edge in edges 
                        if edge.source == return_value or edge.target == return_value
                    ]
                    st.write(f"**连接数:** {len(related_edges)}")
            except Exception as e:
                st.error(f"渲染图表时出错: {e}")
                st.info("请确保已安装: pip install streamlit-agraph")
        
        with col2:
            st.subheader("图例说明")
            
            # 模块图例（如果module列存在）
            if 'module' in nodes_df.columns and module_colors:
                st.write("**模块分类:**")
                for module, color in module_colors.items():
                    if selected_module == '所有模块' or module == selected_module:
                        st.markdown(f"<span style='color:{color}'>●</span> {module}", unsafe_allow_html=True)
            else:
                st.write("**节点:**")
                st.markdown("<span style='color:#1F77B4'>●</span> 所有节点", unsafe_allow_html=True)
            
            st.write("**关系权重:**")
            st.markdown("边越粗表示权重越大")

    # 统计信息
    st.divider()
    st.subheader("网络统计信息")
    
    if nodes and edges:
        col3, col4, col5, col6 = st.columns(4)
        
        with col3:
            st.metric("节点数量", len(nodes))
        
        with col4:
            st.metric("关系数量", len(edges))
        
        with col5:
            if len(nodes) > 1:
                density = (2 * len(edges)) / (len(nodes) * (len(nodes) - 1))
                st.metric("网络密度", f"{density:.3f}")
            else:
                st.metric("网络密度", "N/A")
        
        with col6:
            avg_degree = (2 * len(edges)) / len(nodes)
            st.metric("平均度数", f"{avg_degree:.2f}")

else:
    st.error("无法加载数据，请检查文件是否存在")
    st.markdown("""
    ### 需要的文件:
    
    请确保以下文件存在于同一目录下:
    
    **nodes.csv** - 包含列: `id`, `module`, `label`
    **edges.csv** - 包含列: `source`, `target`, `weight`
    """)

# 安装说明
with st.sidebar:
    st.divider()
    st.subheader("安装说明")
    st.code("pip install streamlit streamlit-agraph pandas", language="bash")