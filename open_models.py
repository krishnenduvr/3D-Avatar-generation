import base64
import json
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="Open Models",
    layout="wide",
    initial_sidebar_state="collapsed",
)


MAIN_MODEL_FILES = [
    {
        "title": "Ananya GLB",
        "path": Path("ananya.glb"),
        "kind": "glb",
        "mime_type": "model/gltf-binary",
        "accent": "#8B5E3C",
    }
]


EXTRA_MODEL_FILES = [
    {
        "title": "Medha",
        "path": Path("13.glb"),
        "kind": "glb",
        "mime_type": "model/gltf-binary",
        "accent": "#F97360",
    },
    {
        "title": "Akshaya",
        "path": Path("25.glb"),
        "kind": "glb",
        "mime_type": "model/gltf-binary",
        "accent": "#4B7BEC",
    },
]


@st.cache_data(show_spinner=False)
def load_model_base64(path_str: str) -> str:
    return base64.b64encode(Path(path_str).read_bytes()).decode("ascii")


def format_size(num_bytes: int) -> str:
    size = float(num_bytes)
    for unit in ["B", "KB", "MB", "GB"]:
        if size < 1024 or unit == "GB":
            return f"{size:.1f} {unit}" if unit != "B" else f"{int(size)} {unit}"
        size /= 1024
    return f"{size:.1f} GB"


def build_model_config(model: dict) -> dict:
    size_bytes = model["path"].stat().st_size
    return {
        "title": model["title"],
        "filename": model["path"].name,
        "kind": model["kind"],
        "accent": model["accent"],
        "mime_type": model["mime_type"],
        "size_label": format_size(size_bytes),
        "base64_data": load_model_base64(str(model["path"])),
    }


def build_viewer_html(
    config: dict,
    viewer_label: str,
    viewer_height: int,
    show_tip: bool,
) -> str:
    html = """
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <style>
    :root {
      --panel: rgba(10, 14, 24, 0.74);
      --line: rgba(255, 255, 255, 0.12);
      --text: #f6f3ff;
      --muted: rgba(231, 235, 255, 0.74);
      --accent: __ACCENT__;
      --bg-top: #131a30;
      --bg-bottom: #050811;
    }
    html, body {
      margin: 0;
      padding: 0;
      overflow: hidden;
      background: transparent;
      font-family: "Trebuchet MS", "Segoe UI", sans-serif;
      color: var(--text);
    }
    .viewer-shell {
      position: relative;
      width: 100%;
      height: __VIEWER_HEIGHT__px;
      overflow: hidden;
      border-radius: 24px;
      background:
        radial-gradient(circle at 18% 20%, rgba(87, 133, 255, 0.28), transparent 28%),
        radial-gradient(circle at 82% 16%, rgba(255, 90, 155, 0.24), transparent 26%),
        radial-gradient(circle at 50% 100%, rgba(98, 255, 214, 0.12), transparent 32%),
        linear-gradient(180deg, var(--bg-top), var(--bg-bottom));
      border: 1px solid rgba(255,255,255,0.08);
      box-shadow:
        inset 0 1px 0 rgba(255,255,255,0.08),
        0 22px 48px rgba(0, 0, 0, 0.42);
    }
    #stage {
      width: 100%;
      height: 100%;
      display: block;
    }
    .hud {
      position: absolute;
      top: 16px;
      left: 16px;
      display: grid;
      gap: 10px;
      width: auto;
      max-width: calc(100% - 32px);
      pointer-events: none;
    }
    .card {
      width: fit-content;
      max-width: 240px;
      padding: 9px 11px;
      border-radius: 14px;
      background: var(--panel);
      border: 1px solid var(--line);
      backdrop-filter: blur(16px);
      box-shadow: 0 12px 28px rgba(0, 0, 0, 0.22);
      pointer-events: auto;
    }
    .eyebrow {
      display: inline-block;
      margin-bottom: 4px;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 0.08em;
      text-transform: uppercase;
      color: var(--accent);
    }
    .title {
      margin: 0;
      font-size: 15px;
      line-height: 1.2;
    }
    .meta {
      margin-top: 3px;
      font-size: 11px;
      color: var(--muted);
      line-height: 1.3;
    }
    .tip {
      position: absolute;
      left: 16px;
      bottom: 16px;
      right: 16px;
      width: fit-content;
      max-width: calc(100% - 32px);
      padding: 10px 14px;
      border-radius: 999px;
      background: rgba(8, 12, 22, 0.7);
      color: rgba(255,255,255,0.9);
      font-size: 12px;
      border: 1px solid rgba(255,255,255,0.08);
      backdrop-filter: blur(8px);
    }
    .status {
      position: absolute;
      top: 16px;
      right: 16px;
      padding: 10px 14px;
      border-radius: 999px;
      background: rgba(8, 12, 22, 0.52);
      border: 1px solid rgba(255,255,255,0.08);
      font-size: 12px;
      color: var(--muted);
      backdrop-filter: blur(8px);
      max-width: calc(100% - 32px);
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }
  </style>
</head>
<body>
  <div class="viewer-shell">
    <canvas id="stage"></canvas>
    <div class="hud">
      <div class="card">
        <span class="eyebrow">__VIEWER_LABEL__</span>
        <h2 class="title" id="title"></h2>
        <div class="meta" id="meta"></div>
      </div>
    </div>
    <div class="status" id="status">Loading model...</div>
    __VIEWER_TIP__
  </div>

  <script type="module">
    import * as THREE from "https://unpkg.com/three@0.161.0/build/three.module.js?module";
    import { OrbitControls } from "https://unpkg.com/three@0.161.0/examples/jsm/controls/OrbitControls.js?module";
    import { GLTFLoader } from "https://unpkg.com/three@0.161.0/examples/jsm/loaders/GLTFLoader.js?module";
    import { STLLoader } from "https://unpkg.com/three@0.161.0/examples/jsm/loaders/STLLoader.js?module";

    const config = __CONFIG_JSON__;
    const canvas = document.getElementById("stage");
    const title = document.getElementById("title");
    const meta = document.getElementById("meta");
    const status = document.getElementById("status");

    title.textContent = config.title;
    meta.innerHTML =
      config.filename +
      "<br/>" +
      config.kind.toUpperCase() +
      " file | " +
      config.size_label;

    const renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true
    });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;

    const scene = new THREE.Scene();
    scene.background = null;

    const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
    camera.position.set(0.8, 1.3, 4.3);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.target.set(0, 0.5, 0);
    controls.minDistance = 1.2;
    controls.maxDistance = 12;

    const hemiLight = new THREE.HemisphereLight(0xf7f5ff, 0x101827, 1.5);
    scene.add(hemiLight);

    const keyLight = new THREE.DirectionalLight(0xffffff, 2.4);
    keyLight.position.set(3.2, 5.6, 4.6);
    scene.add(keyLight);

    const fillLight = new THREE.DirectionalLight(0x8cb8ff, 1.35);
    fillLight.position.set(-3.5, 2.8, -2.4);
    scene.add(fillLight);

    const rimLight = new THREE.PointLight(config.accent, 18, 10, 2);
    rimLight.position.set(0, 1.8, -2.4);
    scene.add(rimLight);

    const stage = new THREE.Mesh(
      new THREE.CylinderGeometry(1.45, 1.7, 0.18, 64),
      new THREE.MeshStandardMaterial({
        color: 0x0e1627,
        roughness: 0.5,
        metalness: 0.28
      })
    );
    stage.position.y = -0.55;
    stage.receiveShadow = true;
    scene.add(stage);

    const accentRing = new THREE.Mesh(
      new THREE.TorusGeometry(1.3, 0.035, 18, 80),
      new THREE.MeshStandardMaterial({
        color: config.accent,
        emissive: new THREE.Color(config.accent),
        emissiveIntensity: 1.25,
        roughness: 0.24,
        metalness: 0.2
      })
    );
    accentRing.rotation.x = Math.PI / 2;
    accentRing.position.y = -0.45;
    scene.add(accentRing);

    const outerRing = new THREE.Mesh(
      new THREE.TorusGeometry(1.52, 0.028, 18, 100),
      new THREE.MeshStandardMaterial({
        color: 0xffffff,
        emissive: new THREE.Color(config.accent),
        emissiveIntensity: 0.55,
        transparent: true,
        opacity: 0.85
      })
    );
    outerRing.rotation.x = Math.PI / 2;
    outerRing.position.y = -0.47;
    scene.add(outerRing);

    const shadowPlane = new THREE.Mesh(
      new THREE.CircleGeometry(1.35, 64),
      new THREE.MeshBasicMaterial({
        color: 0x06080f,
        transparent: true,
        opacity: 0.22
      })
    );
    shadowPlane.rotation.x = -Math.PI / 2;
    shadowPlane.position.y = -0.458;
    scene.add(shadowPlane);

    const glowPlane = new THREE.Mesh(
      new THREE.CircleGeometry(1.85, 64),
      new THREE.MeshBasicMaterial({
        color: new THREE.Color(config.accent),
        transparent: true,
        opacity: 0.18
      })
    );
    glowPlane.rotation.x = -Math.PI / 2;
    glowPlane.position.y = -0.535;
    scene.add(glowPlane);

    const pivot = new THREE.Group();
    scene.add(pivot);

    function resize() {
      const width = canvas.clientWidth || canvas.parentElement.clientWidth || 1;
      const height = canvas.clientHeight || canvas.parentElement.clientHeight || 1;
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    }

    function decodeBase64(base64Text) {
      const binary = atob(base64Text);
      const bytes = new Uint8Array(binary.length);
      for (let index = 0; index < binary.length; index += 1) {
        bytes[index] = binary.charCodeAt(index);
      }
      return bytes.buffer;
    }

    function centerAndScale(object3d) {
      const box = new THREE.Box3().setFromObject(object3d);
      const size = box.getSize(new THREE.Vector3());
      const center = box.getCenter(new THREE.Vector3());
      const maxSide = Math.max(size.x, size.y, size.z) || 1;
      const scale = 2.2 / maxSide;

      object3d.position.sub(center);
      object3d.scale.setScalar(scale);

      const scaledBox = new THREE.Box3().setFromObject(object3d);
      const minY = scaledBox.min.y;
      object3d.position.y -= minY + 0.45;

      const finalBox = new THREE.Box3().setFromObject(object3d);
      const finalSize = finalBox.getSize(new THREE.Vector3());
      controls.target.set(0, Math.max(0.2, finalSize.y * 0.34), 0);
      controls.update();
    }

    function frameCamera(object3d) {
      const box = new THREE.Box3().setFromObject(object3d);
      const size = box.getSize(new THREE.Vector3());
      const maxDim = Math.max(size.x, size.y, size.z) || 1;
      const fitHeightDistance = (maxDim * 0.5) / Math.tan(THREE.MathUtils.degToRad(camera.fov * 0.5));
      const distance = Math.max(2.4, fitHeightDistance * 1.45);
      camera.near = Math.max(0.01, distance / 100);
      camera.far = Math.max(100, distance * 100);
      camera.position.set(maxDim * 0.42, Math.max(0.65, size.y * 0.46), distance);
      camera.updateProjectionMatrix();
      controls.update();
    }

    function createVisibleFallbackMaterial(sourceMaterial) {
      const baseColor = sourceMaterial && sourceMaterial.color
        ? sourceMaterial.color.clone()
        : new THREE.Color(config.accent);
      const nextMaterial = new THREE.MeshBasicMaterial({
        color: baseColor,
        map: sourceMaterial && sourceMaterial.map ? sourceMaterial.map : null,
        side: THREE.DoubleSide,
        transparent: false
      });
      if (nextMaterial.map) {
        nextMaterial.map.colorSpace = THREE.SRGBColorSpace;
        nextMaterial.needsUpdate = true;
      }
      return nextMaterial;
    }

    function prepareMaterial(material, missingNormals) {
      const nextMaterial = missingNormals
        ? createVisibleFallbackMaterial(material)
        : (material && material.clone ? material.clone() : material);

      nextMaterial.side = THREE.DoubleSide;
      nextMaterial.transparent = false;
      nextMaterial.opacity = 1;
      if (nextMaterial.map) {
        nextMaterial.map.colorSpace = THREE.SRGBColorSpace;
      }
      if ("roughness" in nextMaterial) {
        nextMaterial.roughness = nextMaterial.roughness ?? 0.7;
      }
      if ("metalness" in nextMaterial) {
        nextMaterial.metalness = nextMaterial.metalness ?? 0.08;
      }
      nextMaterial.needsUpdate = true;
      return nextMaterial;
    }

    function applyModelMaterials(root) {
      root.traverse((node) => {
        if (!node.isMesh) {
          return;
        }
        node.castShadow = true;
        node.receiveShadow = true;
        const missingNormals = !(node.geometry && node.geometry.attributes.normal);
        if (node.geometry && missingNormals) {
          node.geometry.computeVertexNormals();
        }
        if (!node.material) {
          node.material = new THREE.MeshStandardMaterial({
            color: config.accent,
            roughness: 0.66,
            metalness: 0.08,
            side: THREE.DoubleSide
          });
          return;
        }
        if (Array.isArray(node.material)) {
          node.material = node.material.map((material) =>
            prepareMaterial(material, missingNormals)
          );
          return;
        }
        node.material = prepareMaterial(node.material, missingNormals);
      });
    }

    async function loadModel() {
      const buffer = decodeBase64(config.base64_data);

      if (config.kind === "glb") {
        const loader = new GLTFLoader();
        const gltf = await new Promise((resolve, reject) => {
          loader.parse(buffer, "", resolve, reject);
        });
        const root = gltf.scene || gltf.scenes[0];
        applyModelMaterials(root);
        pivot.add(root);
        centerAndScale(root);
        frameCamera(root);
        return;
      }

      const geometry = new STLLoader().parse(buffer);
      geometry.computeVertexNormals();
      const material = new THREE.MeshStandardMaterial({
        color: config.accent,
        roughness: 0.58,
        metalness: 0.12
      });
      const mesh = new THREE.Mesh(geometry, material);
      mesh.castShadow = true;
      mesh.receiveShadow = true;
      pivot.add(mesh);
      centerAndScale(mesh);
      frameCamera(mesh);
    }

    function animate() {
      requestAnimationFrame(animate);
      pivot.rotation.y += 0.0032;
      controls.update();
      renderer.render(scene, camera);
    }

    window.addEventListener("resize", resize);
    resize();

    loadModel()
      .then(() => {
        status.textContent = config.filename;
        animate();
      })
      .catch((error) => {
        console.error(error);
        status.textContent = "Unable to load this model";
      });
  </script>
</body>
</html>
    """
    viewer_tip_html = (
        '<div class="tip">Drag to orbit. Scroll to zoom. Right-drag to pan.</div>'
        if show_tip
        else ""
    )
    return (
        html.replace("__CONFIG_JSON__", json.dumps(config))
        .replace("__ACCENT__", config["accent"])
        .replace("__VIEWER_LABEL__", viewer_label)
        .replace("__VIEWER_HEIGHT__", str(viewer_height))
        .replace("__VIEWER_TIP__", viewer_tip_html)
    )


def build_model_card_html(model: dict, subtitle: str, eyebrow: str) -> str:
    return """
    <div class="model-card" style="--accent:{accent};">
      <div class="model-eyebrow">{eyebrow}</div>
      <div class="model-name">{title}</div>
      <div class="model-meta">{subtitle}</div>
    </div>
    """.format(
        accent=model["accent"],
        eyebrow=eyebrow,
        title=model["title"],
        subtitle=subtitle,
    )


st.markdown(
    """
    <style>
      [data-testid="stSidebar"] {
        display: none;
      }
      [data-testid="collapsedControl"] {
        display: none;
      }
      header[data-testid="stHeader"] {
        background: transparent;
      }
      
      [data-testid="stAppViewContainer"] {
        background: #FFF9C4;  /* light yellow */
        }
      

      .block-container {
        padding-top: 1rem;
        padding-bottom: 2.4rem;
        max-width: 1320px;
      }
      [data-baseweb="tab-list"] {
        gap: 0.55rem;
        margin-top: 0.5rem;
        margin-bottom: 1rem;
      }
      [data-baseweb="tab"] {
        height: 46px;
        padding: 0 1rem;
        border-radius: 999px;
        background: rgba(12, 18, 32, 0.86);
        border: 1px solid rgba(255, 255, 255, 0.08);
        color: #d5defa;
        font-weight: 700;
      }
      [data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #4f7cff, #ff5c91);
        color: white;
        box-shadow: 0 14px 28px rgba(79, 124, 255, 0.26);
      }
      .hero-shell {
        position: relative;
        overflow: hidden;
        padding: 1.55rem 1.6rem;
        border-radius: 32px;
        background:
          radial-gradient(circle at top right, rgba(255,255,255,0.08), transparent 24%),
          linear-gradient(135deg, rgba(17, 24, 39, 0.98), rgba(23, 33, 58, 0.96) 48%, rgba(49, 46, 129, 0.92) 100%);
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 28px 60px rgba(0, 0, 0, 0.32);
        margin-bottom: 1rem;
      }
      .hero-kicker {
        font-size: 0.78rem;
        font-weight: 800;
        letter-spacing: 0.14em;
        text-transform: uppercase;
        color: rgba(255,255,255,0.84);
      }
      .hero-title {
        margin: 0.35rem 0 0;
        max-width: 780px;
        font-size: 2.25rem;
        line-height: 1.04;
        color: white;
      }
      .hero-copy {
        margin: 0.8rem 0 0;
        max-width: 760px;
        color: rgba(255,255,255,0.9);
        font-size: 1rem;
        line-height: 1.6;
      }
      .hero-badges {
        display: flex;
        flex-wrap: wrap;
        gap: 0.65rem;
        margin-top: 1rem;
      }
      .hero-badge {
        padding: 0.48rem 0.8rem;
        border-radius: 999px;
        background: rgba(255,255,255,0.2);
        border: 1px solid rgba(255,255,255,0.26);
        color: white;
        font-size: 0.9rem;
        font-weight: 700;
      }
      .model-card {
        padding: 1rem 1.05rem;
        border-radius: 24px;
        background:
          linear-gradient(180deg, rgba(12,18,32,0.88), rgba(16,24,40,0.78));
        border-left: 6px solid var(--accent);
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 18px 36px rgba(0, 0, 0, 0.24);
        margin-bottom: 0.7rem;
      }
      .model-eyebrow {
        font-size: 0.73rem;
        font-weight: 800;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        color: var(--accent);
      }
      .model-name {
        margin-top: 0.2rem;
        font-size: 1.08rem;
        font-weight: 800;
        color: #eef2ff;
      }
      .model-meta {
        margin-top: 0.25rem;
        font-size: 0.9rem;
        color: #b8c2dc;
      }
      .section-title {
        margin-top: 0.2rem;
        font-size: 1.45rem;
        font-weight: 800;
        color: #f3f5ff;
      }
      .section-copy {
        margin-top: 0.2rem;
        margin-bottom: 0.95rem;
        color: #b8c2dc;
      }
      @media (max-width: 900px) {
        .hero-title {
          font-size: 1.9rem;
        }
      }
    </style>
    """,
    unsafe_allow_html=True,
)

available_main_models = [model for model in MAIN_MODEL_FILES if model["path"].exists()]
missing_main_models = [model for model in MAIN_MODEL_FILES if not model["path"].exists()]
medha_model = next((model for model in EXTRA_MODEL_FILES if model["path"].name == "13.glb"), None)
akshaya_model = next((model for model in EXTRA_MODEL_FILES if model["path"].name == "25.glb"), None)

st.markdown(
    """
    <div class="hero-shell">
      <div class="hero-kicker">Avatar Studio</div>
      <h1 class="hero-title">3D avatar showroom</h1>
      <p class="hero-copy">
        Meet Anaya, Medha, and Akshaya—three distinct avatars, each shining on their own vibrant stage.
      </p>
      <div class="hero-badges">
        <span class="hero-badge">Realistic 3D Avatars</span>
        <span class="hero-badge">Interactive Viewer</span>
        <span class="hero-badge">Rotate • Zoom • Explore</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

page_tabs = st.tabs(["🧍 Anaya", "🧍 Medha", "🧍 Akshaya"])

with page_tabs[0]:
    st.markdown('<div class="section-title">Anaya</div>', unsafe_allow_html=True)
    for model in MAIN_MODEL_FILES:
            st.markdown(
                build_model_card_html(
                    model,
                    subtitle=model["path"].name,
                    eyebrow="Avatar",
                ),
                unsafe_allow_html=True,
            )
            if model["path"].exists():
                config = build_model_config(model)
                components.html(
                    build_viewer_html(
                        config,
                        viewer_label=model["title"],
                        viewer_height=560,
                        show_tip=True,
                    ),
                    height=580,
                )
            else:
                st.error(f"Missing file: {model['path'].name}")

    if missing_main_models:
        st.caption(
            "Missing main files: "
            + ", ".join(model["path"].name for model in missing_main_models)
        )

with page_tabs[1]:
    st.markdown('<div class="section-title">Medha</div>', unsafe_allow_html=True)
    if medha_model and medha_model["path"].exists():
        medha_config = build_model_config(medha_model)
        st.markdown(
            build_model_card_html(
                medha_model,
                subtitle=f"{medha_model['path'].name} | {medha_config['size_label']}",
                eyebrow="Avatar",
            ),
            unsafe_allow_html=True,
        )
        components.html(
            build_viewer_html(
                medha_config,
                viewer_label="Medha",
                viewer_height=560,
                show_tip=True,
            ),
            height=580,
        )
    else:
        st.error("Missing file: `13.glb`")

with page_tabs[2]:
    st.markdown('<div class="section-title">Akshaya</div>', unsafe_allow_html=True)
    if akshaya_model and akshaya_model["path"].exists():
        akshaya_config = build_model_config(akshaya_model)
        st.markdown(
            build_model_card_html(
                akshaya_model,
                subtitle=f"{akshaya_model['path'].name} | {akshaya_config['size_label']}",
                eyebrow="Avatar",
            ),
            unsafe_allow_html=True,
        )
        components.html(
            build_viewer_html(
                akshaya_config,
                viewer_label="Akshaya",
                viewer_height=560,
                show_tip=True,
            ),
            height=580,
        )
    else:
        st.error("Missing file: `25.glb`")
