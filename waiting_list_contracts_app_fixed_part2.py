# الجزء الثاني من النسخة المحسنة - واجهات المستخدم

# ---------------------------- واجهة الدخول ---------------------------- #
def login_ui() -> None:
    """واجهة تسجيل الدخول المحسنة"""
    banner_path = None
    for ext in ['.png', '.jpg', '.jpeg']:
        path = Path(f"static/banner{ext}")
        if path.exists():
            banner_path = path
            break
    
    if banner_path:
        try:
            with open(banner_path, "rb") as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode()
            st.markdown(
                f"<div style='text-align: center;'><img src='data:image/png;base64,{encoded_string}' class='banner-image'></div>",
                unsafe_allow_html=True
            )
        except Exception as e:
            st.error(f"خطأ في تحميل الصورة: {e}")
    
    st.markdown(f"<div class='header'><h1>{APP_TITLE}</h1></div>", unsafe_allow_html=True)
    
    with st.form("login_form"):
        st.markdown("### تسجيل الدخول")
        username = st.text_input("اسم المستخدم", max_chars=50)
        password = st.text_input("كلمة المرور", type="password", max_chars=100)
        
        if st.form_submit_button("تسجيل الدخول"):
            if not username or not password:
                st.error("يرجى إدخال اسم المستخدم وكلمة المرور")
                return
            
            try:
                with get_conn() as conn:
                    # البحث عن المستخدم
                    hospital_user = conn.execute(
                        "SELECT * FROM hospitals WHERE username=?", (username,)
                    ).fetchone()
                    admin_user = conn.execute(
                        "SELECT * FROM admins WHERE username=?", (username,)
                    ).fetchone()
                    
                    user_data = hospital_user or admin_user
                    table_name = "hospitals" if hospital_user else "admins"
                    
                    if user_data and verify_password(password, user_data['password_hash']):
                        # تحديث كلمة المرور إذا كانت بالتشفير القديم
                        if not user_data['password_hash'].startswith('$2b$'):
                            new_hash = secure_hash(password)
                            conn.execute(
                                f"UPDATE {table_name} SET password_hash=? WHERE id=?",
                                (new_hash, user_data['id'])
                            )
                            conn.commit()
                        
                        role = "hospital" if hospital_user else user_data["role"]
                        st.session_state.user = {"role": role, **dict(user_data)}
                        log_activity("تسجيل الدخول")
                        st.success("تم تسجيل الدخول بنجاح")
                        st.rerun()
                    else:
                        # تأخير بسيط لمنع هجمات التوقيت
                        time.sleep(0.5)
                        st.error("اسم المستخدم أو كلمة المرور غير صحيحة")
            except Exception as e:
                st.error(f"خطأ في تسجيل الدخول: {e}")

# ---------------------------- صفحات المستشفى ---------------------------- #
def hospital_home() -> None:
    """الصفحة الرئيسية للمستشفى"""
    user = st.session_state.user
    logo_path = Path("static/logo.png")
    if logo_path.exists():
        st.sidebar.image(str(logo_path), width=80)
    
    st.sidebar.markdown(f"### أهلاً بك")
    st.sidebar.markdown(f"**{user['name']}**")
    st.sidebar.markdown("---")
    
    menu_items = [
        "🏠 الصفحة الرئيسية", "📝 تقديم طلب جديد", "📂 طلباتي",
        "📥 ملفات للتنزيل", "🔑 تغيير كلمة المرور", "🚪 تسجيل الخروج"
    ]
    menu_icons = ["house-fill", "file-earmark-plus-fill", "folder-fill", "download", "key-fill", "box-arrow-right"]
    
    with st.sidebar:
        selection = option_menu(None, menu_items, icons=menu_icons, menu_icon="cast", default_index=0)
    
    menu_options = {
        "🏠 الصفحة الرئيسية": hospital_dashboard_ui,
        "📝 تقديم طلب جديد": hospital_new_request_ui,
        "📂 طلباتي": hospital_requests_ui,
        "📥 ملفات للتنزيل": lambda u: resources_download_ui(),
        "🔑 تغيير كلمة المرور": lambda u: change_password_ui(user_id=u["id"], user_table="hospitals")
    }
    
    if selection == "🚪 تسجيل الخروج":
        st.session_state.clear()
        st.rerun()
    else:
        menu_options[selection](user)

def hospital_dashboard_ui(user: Dict[str, Any]) -> None:
    """لوحة تحكم المستشفى"""
    st.markdown("<div class='subheader'>ملف المستشفى</div>", unsafe_allow_html=True)
    
    if st.session_state.get("profile_update_success"):
        st.success("تم تحديث بياناتك بنجاح. يمكنك الآن تقديم طلبك من القائمة الجانبية.")
        del st.session_state["profile_update_success"]
    
    try:
        with get_conn() as conn:
            hospital = conn.execute("SELECT * FROM hospitals WHERE id=?", (user["id"],)).fetchone()
        
        if not hospital:
            st.error("لم يتم العثور على بيانات المستشفى")
            return
        
        # checkbox خارج الـ form للمستشفيات الخاصة
        no_end_date = False
        if hospital['type'] != 'حكومي':
            current_no_end = hospital['license_end'] == "غير محدد" or not hospital['license_end']
            no_end_date = st.checkbox(
                "ترخيص دائم (بدون تاريخ انتهاء)",
                value=current_no_end,
                key="no_end_date_checkbox"
            )
        
        with st.form("edit_hospital_profile"):
            st.info("يمكنك تحديث بيانات التواصل والترخيص من هنا. لتغيير البيانات الأساسية، يرجى التواصل مع الإدارة.")
            
            col1, col2 = st.columns(2)
            with col1:
                st.text_input("اسم المستشفى", value=hospital['name'], disabled=True)
                st.text_input("القطاع", value=hospital['sector'] or "", disabled=True)
                st.text_input("المحافظة", value=hospital['governorate'] or "", disabled=True)
            with col2:
                st.text_input("كود المستشفى", value=hospital['code'], disabled=True)
                st.text_input("نوع المستشفى", value=hospital['type'] or "", disabled=True)
            
            st.markdown("---")
            
            col3, col4 = st.columns(2)
            with col3:
                if hospital['type'] != 'حكومي':
                    license_start = st.date_input(
                        "بداية الترخيص",
                        value=parse_date_safely(hospital['license_start']),
                        min_value=date(1900, 1, 1),
                        max_value=date(2100, 12, 31)
                    )
                    license_number = st.text_input("رقم الترخيص", value=hospital['license_number'] or "")
                else:
                    license_start = None
                    license_number = st.text_input("رقم الترخيص (اختياري)", value=hospital['license_number'] or "")
                
                manager_name = st.text_input("مدير المستشفى", value=hospital['manager_name'] or "")
            
            with col4:
                if hospital['type'] != 'حكومي':
                    if not no_end_date:
                        license_end = st.date_input(
                            "تاريخ انتهاء الترخيص",
                            value=parse_date_safely(hospital['license_end'], date.today()),
                            min_value=date(1900, 1, 1),
                            max_value=date(2100, 12, 31)
                        )
                    else:
                        license_end = "غير محدد"
                else:
                    license_end = None
                
                manager_phone = st.text_input("هاتف المدير", value=hospital['manager_phone'] or "")
                address = st.text_area("عنوان المستشفى", value=hospital['address'] or "", height=100)
            
            st.markdown("---")
            st.markdown("**معلومات الفروع (اختياري)**")
            col5, col6 = st.columns(2)
            with col5:
                other_branches = st.text_input(
                    "الفروع الأخرى",
                    value=hospital['other_branches'] or "",
                    help="اختياري - أسماء الفروع الأخرى"
                )
            with col6:
                other_branches_address = st.text_area(
                    "عناوين الفروع",
                    value=hospital['other_branches_address'] or "",
                    height=100,
                    help="اختياري - عناوين الفروع الأخرى"
                )
            
            if st.form_submit_button("حفظ البيانات"):
                try:
                    with get_conn() as conn:
                        license_end_value = None
                        if hospital['type'] != 'حكومي':
                            if license_end == "غير محدد":
                                license_end_value = "غير محدد"
                            elif license_end:
                                license_end_value = str(license_end)
                        
                        conn.execute("""
                            UPDATE hospitals SET address=?, license_start=?, license_end=?, 
                            manager_name=?, manager_phone=?, license_number=?, other_branches=?, other_branches_address=? 
                            WHERE id=?
                        """, (
                            address, str(license_start) if license_start else None, license_end_value,
                            manager_name, manager_phone, license_number, other_branches, other_branches_address,
                            user["id"]
                        ))
                        conn.commit()
                    
                    st.session_state["profile_update_success"] = True
                    st.rerun()
                except Exception as e:
                    st.error(f"حدث خطأ: {e}")
    except Exception as e:
        st.error(f"خطأ في تحميل بيانات المستشفى: {e}")

def hospital_new_request_ui(user: Dict[str, Any]) -> None:
    """واجهة تقديم طلب تعاقد جديد"""
    if not is_hospital_profile_complete(user["id"]):
        st.warning("⚠️ يجب إكمال بيانات المستشفى الأساسية أولاً")
        hospital_dashboard_ui(user)
        return
    
    try:
        with get_conn() as conn:
            services = conn.execute(
                "SELECT id, name FROM services WHERE active=1 ORDER BY name"
            ).fetchall()
    except Exception as e:
        st.error(f"خطأ في جلب الخدمات: {e}")
        return
    
    st.markdown("<div class='subheader'>تقديم طلب تعاقد جديد</div>", unsafe_allow_html=True)
    st.markdown("<div class='info-box'>يرجى اختيار الخدمة والفئة العمرية، ثم رفع المستندات المطلوبة.</div>", unsafe_allow_html=True)
    
    with st.form("new_request"):
        service_name = st.selectbox("الخدمة المراد التعاقد عليها", [s["name"] for s in services])
        age_category = st.selectbox("الفئة", AGE_CATEGORIES)
        submitted = st.form_submit_button("إنشاء الطلب")
    
    if submitted:
        service_id = next((s["id"] for s in services if s["name"] == service_name), None)
        if not service_id:
            st.error("خطأ في تحديد الخدمة.")
            return
        
        preventing_statuses = get_preventing_statuses()
        blocking_statuses = get_blocking_statuses()
        
        if hospital_has_open_request(user["id"], service_id, preventing_statuses):
            st.error("لا يمكن إنشاء طلب جديد لنفس الخدمة قبل إغلاق الطلب الحالي من قبل الإدارة.")
            return
        
        if hospital_blocked_from_request(user["id"], service_id, blocking_statuses):
            st.error("لا يمكن تقديم طلب لنفس الخدمة لمدة 3 أشهر من تاريخ رفض الطلب أو إرجاء التعاقد.")
            return
        
        try:
            with get_conn() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO requests (hospital_id, service_id, age_category, status, created_at)
                    VALUES (?,?,?,?,?)
                """, (user["id"], service_id, age_category, "طلب غير مكتمل", datetime.now().isoformat()))
                req_id = cur.lastrowid
                conn.commit()
            
            ensure_request_docs(req_id, user["type"])
            st.success("تم إنشاء الطلب. يمكنك الآن رفع المستندات.")
            st.session_state["active_request_id"] = req_id
            st.session_state[f"editing_request_{req_id}"] = True
            st.rerun()
        except Exception as e:
            st.error(f"خطأ في إنشاء الطلب: {e}")
    
    req_id = st.session_state.get("active_request_id")
    is_editing = st.session_state.get(f"editing_request_{req_id}", False)
    
    if req_id and is_editing:
        documents_upload_ui(req_id, user, is_active_edit=True)

def documents_upload_ui(request_id: int, user: Dict[str, Any], is_active_edit: bool = False) -> None:
    """واجهة رفع المستندات"""
    st.markdown("<div class='subheader'>رفع المستندات المطلوبة</div>", unsafe_allow_html=True)
    
    try:
        with get_conn() as conn:
            docs = conn.execute(
                "SELECT * FROM documents WHERE request_id=? ORDER BY id",
                (request_id,)
            ).fetchall()
    except Exception as e:
        st.error(f"خطأ في جلب المستندات: {e}")
        return
    
    all_required_uploaded = all(doc['satisfied'] for doc in docs if doc['required'])
    
    for doc in docs:
        cols = st.columns([3, 3, 2, 2, 2])
        with cols[0]:
            st.write(f"**{doc['display_name'] or doc['doc_type']}**")
            if doc['required']:
                st.caption("مطلوب")
            else:
                st.caption("اختياري")
        
        with cols[1]:
            allowed_types = ['pdf']
            is_video_allowed_flag = doc.get('is_video_allowed', 0)
            
            video_only = is_video_only_document(doc['doc_type'])
            
            if video_only:
                allowed_types = ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm']
                st.caption("أنواع الملفات المسموحة: فيديو فقط")
            elif is_video_allowed_flag:
                allowed_types.extend(['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm'])
                st.caption("أنواع الملفات المسموحة: PDF ومقاطع فيديو")
            else:
                st.caption("أنواع الملفات المسموحة: PDF فقط")
            
            uploaded = st.file_uploader(
                "رفع ملف",
                type=allowed_types,
                key=f"up_{doc['id']}"
            )
            
            if uploaded is not None:
                if save_uploaded_file(uploaded, user, request_id, doc):
                    st.rerun()
        
        with cols[2]:
            render_file_downloader(doc, key_prefix=f"doc_upload_{doc['id']}")
        
        with cols[3]:
            if doc["file_path"]:
                if st.button("حذف", key=f"del_{doc['id']}"):
                    delete_document_file(doc)
                    st.rerun()
        
        with cols[4]:
            st.write("✅ مستوفى" if doc["satisfied"] else "❌ غير مستوفى")
    
    if is_active_edit:
        if st.button("حفظ الطلب", disabled=not all_required_uploaded):
            if not all_required_uploaded:
                st.error("لا يمكن حفظ الطلب: هناك مستندات مطلوبة لم يتم رفعها.")
            else:
                try:
                    with get_conn() as conn:
                        statuses = get_request_statuses()
                        initial_status = statuses[0] if statuses else "جاري دراسة الطلب ومراجعة الأوراق"
                        conn.execute(
                            "UPDATE requests SET status=?, updated_at=? WHERE id=?",
                            (initial_status, datetime.now().isoformat(), request_id)
                        )
                        conn.commit()
                    
                    log_activity("تقديم طلب مكتمل", f"طلب رقم: {request_id}")
                    st.success("تم حفظ الطلب بنجاح. سيتم مراجعته من قبل الإدارة.")
                    st.session_state.pop("active_request_id", None)
                    st.session_state.pop(f"editing_request_{request_id}", None)
                    st.cache_data.clear()
                    time.sleep(0.5)
                    st.rerun()
                except Exception as e:
                    st.error(f"خطأ في حفظ الطلب: {e}")
        elif not all_required_uploaded:
            st.info("يرجى رفع جميع المستندات المطلوبة لتفعيل زر 'حفظ الطلب'.")

def save_uploaded_file(file, user: Dict[str, Any], request_id: int, doc_row) -> bool:
    """حفظ ملف مرفوع بشكل آمن"""
    if file is None:
        return False
    
    try:
        # التحقق من نوع الملف
        if not check_file_type(file.name, doc_row.get('is_video_allowed', 0)):
            st.error("نوع الملف غير مسموح")
            return False
        
        # التحقق من حجم الملف (50MB كحد أقصى)
        if file.size > 50 * 1024 * 1024:
            st.error("حجم الملف كبير جداً (الحد الأقصى 50MB)")
            return False
        
        hospital_name = user["name"]
        dest_dir = STORAGE_DIR / safe_filename(hospital_name)[:50] / str(request_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        
        file_ext = Path(file.name).suffix.lower()
        fn = f"{safe_filename(doc_row['doc_type'])[:50]}{file_ext}"
        dest_path = dest_dir / fn
        
        # التحقق من أمان المسار
        if not validate_file_path(dest_path):
            st.error("مسار الملف غير آمن")
            return False
        
        # حفظ الملف
        with open(dest_path, "wb") as f:
            f.write(file.getbuffer())
        
        # تحديث قاعدة البيانات
        now_iso = datetime.now().isoformat()
        with get_conn() as conn:
            conn.execute(
                "UPDATE documents SET file_name=?, file_path=?, uploaded_at=?, satisfied=1 WHERE id=?",
                (fn, str(dest_path), now_iso, doc_row["id"])
            )
            conn.execute(
                "UPDATE requests SET updated_at=? WHERE id=?",
                (now_iso, request_id)
            )
            conn.commit()
        
        st.cache_data.clear()
        st.success("تم رفع الملف بنجاح")
        return True
        
    except Exception as e:
        st.error(f"خطأ في حفظ الملف: {e}")
        return False

def delete_document_file(doc) -> None:
    """حذف ملف المستند بشكل آمن"""
    try:
        if doc['file_path'] and validate_file_path(doc['file_path']):
            if os.path.exists(doc['file_path']):
                os.remove(doc['file_path'])
        
        with get_conn() as conn:
            conn.execute(
                "UPDATE documents SET file_name=NULL, file_path=NULL, satisfied=0 WHERE id=?",
                (doc["id"],)
            )
            conn.commit()
        
        st.cache_data.clear()
        st.success("تم حذف الملف")
    except Exception as e:
        st.error(f"خطأ في حذف الملف: {e}")

def render_file_downloader(doc, key_prefix: str = "dl") -> None:
    """عرض زر تنزيل الملف مع التحقق من الأمان"""
    if not doc["file_path"]:
        st.caption("— لم يتم الرفع")
        return
    
    try:
        file_path_obj = Path(doc["file_path"])
        
        # التحقق من أمان المسار
        if not validate_file_path(file_path_obj):
            st.warning("⚠️ مسار الملف غير آمن")
            return
        
        if file_path_obj.exists() and file_path_obj.is_file():
            with open(file_path_obj, "rb") as f:
                st.download_button(
                    "تنزيل",
                    data=f.read(),
                    file_name=file_path_obj.name,
                    key=f"{key_prefix}_{doc['id']}"
                )
        else:
            st.warning("⚠️ الملف غير موجود على الخادم.")
            # مسح المسار غير الصالح من قاعدة البيانات
            with get_conn() as conn:
                conn.execute(
                    "UPDATE documents SET file_name=NULL, file_path=NULL, satisfied=0 WHERE id=?",
                    (doc["id"],)
                )
                conn.commit()
            st.rerun()
    except Exception as e:
        st.error(f"خطأ في الوصول للملف: {e}")

def hospital_requests_ui(user: Dict[str, Any]) -> None:
    """واجهة طلبات المستشفى"""
    st.markdown("<div class='subheader'>طلباتي</div>", unsafe_allow_html=True)
    
    try:
        with get_conn() as conn:
            rows = conn.execute("""
                SELECT r.id, s.name AS service_name, r.status, r.created_at, r.updated_at
                FROM requests r JOIN services s ON s.id=r.service_id
                WHERE r.hospital_id=? ORDER BY r.created_at DESC
            """, (user["id"],)).fetchall()
    except Exception as e:
        st.error(f"خطأ في جلب الطلبات: {e}")
        return
    
    if not rows:
        st.info("لا يوجد لديك طلبات حالية.")
        return
    
    df = pd.DataFrame([dict(r) for r in rows])
    st.dataframe(df, use_container_width=True)
    
    req_ids = [str(r["id"]) for r in rows]
    pick = st.selectbox("اختر طلبًا لعرض تفاصيله", ["—"] + req_ids)
    if pick != "—":
        request_details_ui(int(pick))

def request_details_ui(request_id: int, role: str = "hospital") -> None:
    """واجهة تفاصيل الطلب"""
    try:
        with get_conn() as conn:
            r = conn.execute("""
                SELECT r.*, h.name AS hospital_name, h.code AS hospital_code,
                       h.type AS hospital_type, s.name AS service_name
                FROM requests r
                JOIN hospitals h ON h.id=r.hospital_id
                JOIN services s ON s.id=r.service_id
                WHERE r.id=?
            """, (request_id,)).fetchone()
            
            docs = conn.execute(
                "SELECT * FROM documents WHERE request_id=? ORDER BY id",
                (request_id,)
            ).fetchall()
    except Exception as e:
        st.error(f"خطأ في جلب تفاصيل الطلب: {e}")
        return
    
    if not r:
        st.error("الطلب غير موجود.")
        return
    
    st.markdown(f"<div class='subheader'>تفاصيل الطلب #{request_id}</div>", unsafe_allow_html=True)
    st.write(f"**المستشفى:** {r['hospital_name']} — ({r['hospital_code']}) — **النوع:** {r['hospital_type']} — **الخدمة:** {r['service_name']} — **الفئة:** {r['age_category']}")
    
    # عرض تواريخ الطلب
    try:
        created_at_dt = datetime.fromisoformat(r['created_at'])
        info_text = f"**تاريخ التقديم:** {created_at_dt.strftime('%Y-%m-%d %H:%M:%S')}"
        
        if r['updated_at']:
            updated_at_dt = datetime.fromisoformat(r['updated_at'])
            if (updated_at_dt - created_at_dt).total_seconds() > 1:
                updated_at_str = updated_at_dt.strftime('%Y-%m-%d %H:%M:%S')
                info_text += f"  \n**آخر تعديل:** {updated_at_str}"
            else:
                info_text += "  \n*(لم يتم التعديل بعد)*"
        else:
            info_text += "  \n*(لم يتم التعديل بعد)*"
        
        st.info(info_text)
    except Exception:
        st.info(f"**تاريخ التقديم:** {r['created_at']}  \n**آخر تعديل:** {r['updated_at'] or '(لم يتم التعديل بعد)'}")
    
    can_edit = r['status'] in ["طلب غير مكتمل", "جاري دراسة الطلب ومراجعة الأوراق", "يجب استيفاء متطلبات التعاقد"]
    can_delete = r['status'] in ["طلب غير مكتمل", "جاري دراسة الطلب ومراجعة الأوراق", "يجب استيفاء متطلبات التعاقد"]
    
    if can_delete and role == "hospital":
        if st.button("🗑️ حذف الطلب"):
            delete_request(request_id, docs)
            st.rerun()
    
    if can_edit and role == "hospital":
        if st.button("✏️ تعديل الطلب"):
            st.session_state[f"editing_request_{request_id}"] = True
            st.rerun()
    
    is_editing = st.session_state.get(f"editing_request_{request_id}", False)
    if is_editing:
        documents_upload_ui(request_id, st.session_state.user, is_active_edit=True)
    else:
        display_request_documents_readonly(docs)

def delete_request(request_id: int, docs) -> None:
    """حذف الطلب بشكل آمن"""
    try:
        # حذف الملفات
        for d in docs:
            if d['file_path'] and validate_file_path(d['file_path']) and os.path.exists(d['file_path']):
                try:
                    os.remove(d['file_path'])
                except OSError:
                    pass
        
        # حذف من قاعدة البيانات
        with get_conn() as conn:
            conn.execute("DELETE FROM documents WHERE request_id=?", (request_id,))
            conn.execute("DELETE FROM requests WHERE id=?", (request_id,))
            conn.commit()
        
        log_activity("حذف طلب", f"طلب رقم: {request_id}")
        st.success("تم حذف الطلب بنجاح")
        
        # تنظيف متغيرات الجلسة
        st.session_state.pop("active_request_id", None)
        st.session_state.pop(f"editing_request_{request_id}", None)
        st.cache_data.clear()
    except Exception as e:
        st.error(f"خطأ في حذف الطلب: {e}")

def display_request_documents_readonly(docs: List) -> None:
    """عرض المستندات في وضع القراءة فقط"""
    st.markdown("##### المستندات")
    for d in docs:
        c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 2, 3])
        with c1:
            display_name = d['display_name'] or d['doc_type']
            st.write(display_name)
            st.caption("مطلوب" if d['required'] else "اختياري")
        with c2:
            render_file_downloader(d, key_prefix=f"readonly_{d['id']}")
        with c3:
            st.write("✅ مستوفى" if d["satisfied"] else "❌ غير مستوفى")
        with c4:
            if d['uploaded_at']:
                try:
                    upload_time = datetime.fromisoformat(d['uploaded_at']).strftime('%Y-%m-%d %H:%M:%S')
                    st.write(upload_time)
                except Exception:
                    st.write(d['uploaded_at'])
            else:
                st.write("—")
        with c5:
            st.write(d['admin_comment'] or "")

def resources_download_ui() -> None:
    """واجهة تنزيل الملفات"""
    st.markdown("<div class='subheader'>ملفات متوفرة للتنزيل</div>", unsafe_allow_html=True)
    st.markdown("<div class='info-box'>يمكنك تنزيل النماذج والمتطلبات التالية لمساعدتك في عملية التقديم.</div>", unsafe_allow_html=True)
    
    for filename in RESOURCE_FILES:
        filepath = RESOURCES_DIR / filename
        if filepath.exists():
            try:
                with open(filepath, "rb") as f:
                    st.download_button(
                        label=f"📥 {filename}",
                        data=f,
                        file_name=filename,
                        mime="application/pdf",
                        use_container_width=True
                    )
            except Exception as e:
                st.error(f"خطأ في تحميل الملف {filename}: {e}")
        else:
            st.warning(f"الملف غير متوفر حاليًا: {filename}")

def change_password_ui(user_id: int, user_table: str) -> None:
    """واجهة تغيير كلمة المرور"""
    st.markdown("<div class='subheader'>تغيير كلمة المرور</div>", unsafe_allow_html=True)
    
    with st.form("change_pw"):
        old_pw = st.text_input("كلمة المرور الحالية", type="password", max_chars=100)
        new_pw1 = st.text_input("كلمة المرور الجديدة", type="password", max_chars=100)
        new_pw2 = st.text_input("تأكيد كلمة المرور الجديدة", type="password", max_chars=100)
        
        if st.form_submit_button("تغيير كلمة المرور", use_container_width=True):
            if not all([old_pw, new_pw1, new_pw2]):
                st.warning("يرجى ملء جميع الحقول.")
                return
            
            if new_pw1 != new_pw2:
                st.error("كلمتا المرور الجديدتان غير متطابقتين.")
                return
            
            if len(new_pw1) < 6:
                st.error("كلمة المرور الجديدة يجب أن تكون 6 أحرف على الأقل.")
                return
            
            try:
                with get_conn() as conn:
                    user = conn.execute(
                        f"SELECT password_hash FROM {user_table} WHERE id=?",
                        (user_id,)
                    ).fetchone()
                    
                    if user and verify_password(old_pw, user['password_hash']):
                        new_hash = secure_hash(new_pw1)
                        conn.execute(
                            f"UPDATE {user_table} SET password_hash=? WHERE id=?",
                            (new_hash, user_id)
                        )
                        conn.commit()
                        
                        st.success("تم تغيير كلمة المرور بنجاح.")
                        log_activity("تغيير كلمة المرور")
                        st.info("يرجى تسجيل الدخول مرة أخرى باستخدام كلمة المرور الجديدة.")
                        st.session_state.clear()
                        st.rerun()
                    else:
                        st.error("كلمة المرور الحالية غير صحيحة.")
            except Exception as e:
                st.error(f"خطأ في تغيير كلمة المرور: {e}")