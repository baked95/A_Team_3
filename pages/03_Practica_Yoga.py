import streamlit as st
from inc.basic import sublista, update_semaforo
from inc.config import *
from inc.state_machine import *
from inc.video_stream import *

# @st.experimental_dialog("Tips de Ayuda")
# def tips(postu):
#     st.write(f"A destacar en la postura {postu}")
#     reason = st.text_input("Because...")
#     if st.button("Submit"):
#         st.session_state.vote = {"item": item, "reason": reason}
#         st.rerun()

postura = ""
secuencia_concreta = ""

def video_processor_factory():
    if not postura or not secuencia_concreta:
        st.error("No se ha definido la postura o la secuencia concreta. Asegúrate de que ambos valores estén seleccionados.")
        return None
    model_input = Modelos.YOLO
    user_pose = UserPose(postura, secuencia_concreta)
    user_pose.set_sequence(secuencia_concreta)
    user_pose.set_pose(postura)
    return VideoProcessor(model_input, user_pose)

st.subheader("Practica Posturas", anchor = False, divider="red")

# st.subheader("¡Escoge tu ejercicio!", anchor = False, divider="gray")

secuencias_red = list(TRANSICIONES.keys())
secuencias = secuencias_red + ["Postura concreta"]

cajaselect = st.container(height = 160, border = True)
scol1, scol2, scol3, scol4 = cajaselect.columns(spec = [15, 25, 25, 15],
                                gap = 'small', vertical_alignment = 'top')

scol1_seleccion = scol1.popover("Selecciona tu ejercicio")
scol1_secuencia = scol1_seleccion.selectbox("Escoja su Secuencia", secuencias, index=len(secuencias)-1)
scol1_cajavisos = scol1.empty()
scol3_muestravid = scol3.toggle(label = "TIPS / VIDEO MUESTRA", value = False, )
scol3_postura = scol3.empty()

secuencia_min = "_".join(scol1_secuencia.split(" ")).lower()
cajavideos = st.empty()
vercaja = False
estado_usuario = False

if secuencia_min == "postura_concreta":
    secuencia_concreta = scol1_seleccion.selectbox("¿De qué secuencia quieres practicar una postura?", secuencias_red)
    posturas = sublista(TRANSICIONES, secuencia_concreta)
    postura:str = scol1_seleccion.select_slider("Escoja su postura a practicar:", posturas)
    secuencia_min = "_".join(secuencia_concreta.split(" ")).lower()
    postura_min = "_".join(postura.split(" ")).lower()
    vercaja = True
    video_path = f"{VIDEO_DIR}/{secuencia_min}/{postura_min}.mp4"
    scol2.markdown(f"Modalidad: **:orange[POSTURA CONCRETA]**")
    scol2.markdown(f"Secuencia seleccionada: **:blue[{secuencia_concreta}]**")
else:
    secuencia_concreta = scol1_seleccion.selectbox("¿De qué secuencia quieres practicar una postura?", secuencias_red)
    scol1_seleccion.warning("La selección de SECUENCIA todavía no está disponible.")
    # Se añadirá a postoriori
    vercaja = False
    scol2.markdown(f"Modalidad: **:orange[SECUENCIA COMPLETA]**")
    scol2.markdown(f"Secuencia seleccionada: **:blue[{secuencia_concreta}]**")

if postura:
    scol3_postura = scol3.markdown(f"Postura seleccionada: **:red[{postura}]**")
else:
    scol3_postura = scol3.empty()

scol4_semaforo = scol4.empty()
update_semaforo(estado_usuario, scol4_semaforo)

if vercaja:
    cajavideos = st.container(height = 500, border = True)
    lcol = 25
    rcol = 60
    col1, col2 = cajavideos.columns(spec = [lcol, rcol], gap = 'small', vertical_alignment = 'top')
    if scol3_muestravid:
        col1.write("VideoDemo")
        col1.video(data = video_path, loop = True, autoplay = True, muted = True)
    else:
        col1.write("Aquí vendrán los TIPS") 

    with col2:
        # Preparacion webrtc_streamer
        rtc_configuration = {
            "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
        }
        media_stream_constraints = {
            "video": True,
            "audio": False
        }
        webrtc_ctx = webrtc_streamer(
            key="streamer",
            mode=WebRtcMode.SENDRECV,
            video_frame_callback= video_processor_factory,
            rtc_configuration=rtc_configuration,
            media_stream_constraints=media_stream_constraints,
            async_processing=True
        )
        if webrtc_ctx.state.playing:
            message_box = st.empty()
            while True:
                try:
                    keypoints_result = result_queue.get(timeout=1)
                    if keypoints_result:
                        message_box.write(f"Últimos keypoints: {keypoints_result.keypoints}")
                except queue.Empty:
                    message_box.write("Esperando datos...")
                except Exception as e:
                    st.error(f"Error al recibir datos de la cola: {e}")