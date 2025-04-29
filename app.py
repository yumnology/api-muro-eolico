#   Alfredo Barranco Ahued
#   5 de octubre de 2024
#   ORM para la base de datos de la Pared Eólica para ASE II
#   Versión 2.0

from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from dotenv import load_dotenv
import os
from flask_cors import CORS
from flask_migrate import Migrate
from datetime import date, timedelta
import pytz
from sqlalchemy import cast, Date, func
import threading
import time

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
 
db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Inicializar Flask-Migrate

BASE_URL = '/api/v1'
 
mexico_tz = pytz.timezone('America/Mexico_City')

# -----------------------------------------------------------------------
# MODELOS
# -----------------------------------------------------------------------

class TempWallData(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.DateTime, nullable=False)
    group = db.Column(db.Integer, nullable=False)
    propeller1 = db.Column(db.Float, nullable=False)
    propeller2 = db.Column(db.Float, nullable=False)
    propeller3 = db.Column(db.Float, nullable=False)
    propeller4 = db.Column(db.Float, nullable=False)
    propeller5 = db.Column(db.Float, nullable=False)

    def __init__(self, date, group, propeller1, propeller2, propeller3, propeller4, propeller5):    
        self.date = date
        self.group = group
        self.propeller1 = propeller1
        self.propeller2 = propeller2
        self.propeller3 = propeller3
        self.propeller4 = propeller4
        self.propeller5 = propeller5

    def to_json(self):
        return {
            'id': self.id,  # Siempre es buena idea incluir el id también
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S'),
            'group': self.group,
            'propeller1': self.propeller1,
            'propeller2': self.propeller2,
            'propeller3': self.propeller3,
            'propeller4': self.propeller4,
            'propeller5': self.propeller5,
        }

    def __repr__(self):
        return '<TempWallData %r>' % self.propeller1


class WallData(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.DateTime, nullable=False)
    group = db.Column(db.Integer, nullable=False)
    propeller1 = db.Column(db.Float, nullable=False)
    propeller2 = db.Column(db.Float, nullable=False)
    propeller3 = db.Column(db.Float, nullable=False)
    propeller4 = db.Column(db.Float, nullable=False)
    propeller5 = db.Column(db.Float, nullable=False)

    def __init__(self, date, group, propeller1, propeller2, propeller3, propeller4, propeller5):    
        self.date = date
        self.group = group
        self.propeller1 = propeller1
        self.propeller2 = propeller2
        self.propeller3 = propeller3
        self.propeller4 = propeller4
        self.propeller5 = propeller5

    def to_json(self):
        return {
            'id': self.id,  # Siempre es buena idea incluir el id también
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S'),
            'group': self.group,
            'propeller1': self.propeller1,
            'propeller2': self.propeller2,
            'propeller3': self.propeller3,
            'propeller4': self.propeller4,
            'propeller5': self.propeller5,
        }

    def __repr__(self):
        return '<WallData %r>' % self.propeller1

# -----------------------------------------------------------------------
class TotalDay(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False)
    total = db.Column(db.Float, nullable=False)
    group1 = db.Column(db.Float, nullable=False)
    group2 = db.Column(db.Float, nullable=False)
    group3 = db.Column(db.Float, nullable=False)

    def __init__(self, date, total, group1, group2, group3):
        self.date = date
        self.total = total
        self.group1 = group1
        self.group2 = group2
        self.group3 = group3

    def to_json(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m-%d'),
            'total': self.total,
            'group1': self.group1,
            'group2': self.group2,
            'group3': self.group3
        }

    def __repr__(self):
        return '<TotalDay %r>' % self.total

# -----------------------------------------------------------------------
class TotalMonth(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    date = db.Column(db.Date, nullable=False)
    total = db.Column(db.Float, nullable=False)

    def __init__(self, date, total):
        self.date = date
        self.total = total

    def to_json(self):
        return {
            'id': self.id,
            'date': self.date.strftime('%Y-%m'),
            'total': self.total
        }

    def __repr__(self):
        return '<TotalMonth %r>' % self.total
# -----------------------------------------------------------------------
class TotalAll(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    total = db.Column(db.Float, nullable=False)

    def __init__(self, total):
        self.total = total

    def to_json(self):
        return {
            'id': self.id,
            'total': self.total
        }

    def __repr__(self):
        return '<TotalAll %r>' % self.total

class SystemStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    status = db.Column(db.Integer, nullable=False, default=0)  # 0 = offline, 1 = online
    last_update = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(pytz.utc))  # Guardar en UTC

    def __init__(self, status):
        self.status = status
        self.last_update = datetime.now(pytz.utc)  # Guardar en UTC

    def to_json(self):
        # Convertir la fecha UTC almacenada a la zona horaria de México antes de enviarla
        last_update_mx = self.last_update.replace(tzinfo=pytz.utc).astimezone(mexico_tz)
        return {
            "id": self.id,
            "status": self.status,
            "lastUpdate": last_update_mx.strftime('%Y-%m-%d %H:%M:%S')
        }



# -----------------------------------------------------------------------
# INICIO DE | FUNCIONES
# -----------------------------------------------------------------------

def update_total_day(today, total_sum, sum_group1, sum_group2, sum_group3):

    today_object = TotalDay.query.filter_by(date=today).first()

    # Si no existe un objeto con la fecha de hoy, crear uno nuevo
    if today_object is None:
        new_total_day = TotalDay(date=today, total=total_sum, group1=sum_group1, group2=sum_group2, group3=sum_group3)
        db.session.add(new_total_day)
        db.session.commit()
    
    # Si ya existe un objeto con la fecha de hoy, actualizarlo
    else:
        today_object.total += total_sum
        today_object.group1 += sum_group1
        today_object.group2 += sum_group2
        today_object.group3 += sum_group3
        db.session.commit()
# -----------------------------------------------------------------------
def update_total_month(month, total_sum):
    # Ensure month is a datetime object and convert to Mexico City timezone
    if isinstance(month, str):
        month = datetime.strptime(month, '%Y-%m')
    month = mexico_tz.localize(month)

    # Use the first day of the month for the query
    month_start = month.replace(day=1).date()

    month_object = TotalMonth.query.filter_by(date=month_start).first()


    print(month_start)

    print(month_object)
    # If no object exists with the given date, create a new one
    if month_object is None:
        new_total_month = TotalMonth(date=month_start, total=total_sum)
        db.session.add(new_total_month)
        db.session.commit()
    
    # If an object already exists with the given date, update it
    else:
        month_object.total += total_sum
        db.session.commit()

# -----------------------------------------------------------------------
def update_total_all(total_sum):

    total_object = TotalAll.query.first()

    # Si no existe un objeto crear uno nuevo
    # Esto solo debería pasar la primera vez que se corre el programa
    if total_object is None:
        new_total_all = TotalAll(total=total_sum)
        db.session.add(new_total_all)
        db.session.commit()
    
    # Si ya existe un objeto con la fecha de hoy, actualizarlo
    else:
        total_object.total += total_sum
        db.session.commit()

# -----------------------------------------------------------------------
# FIN DE | FUNCIONES
# -----------------------------------------------------------------------

# --- MAIN -------------------------------------------------------------
@app.route('/')
def index():
    return "Welcome to my ORM app!"
 
# ---POST---------------------------------------------------------------

@app.route(BASE_URL + '/new', methods=['POST'])
def create():

    # Definir la fecha de hoy
    date = datetime.now(mexico_tz) # Fecha que irá en WallData

    date_time = date.strftime('%Y-%m-%d %H:%M:%S') # Fecha que irá en WallData
    today = date.strftime('%Y-%m-%d') # Fecha que irá en TotalDay
    month = date.strftime('%Y-%m') # Fecha que irá en TotalMonth

    print(date)
    # Obtener los datos del request
    data = request.get_json()

    if not request.json or 'propeller1' not in request.json:
        abort(400)

    else:

        # Sacar el total generado para actualizar los demás
        total_sum = data['propeller1'] + data['propeller2'] + data['propeller3'] + data['propeller4'] + data['propeller5']

        # Crear un nuevo objeto WallData
        new_wall_data = WallData(
            date=date_time,
            group=data['group'],
            propeller1=data['propeller1'],
            propeller2=data['propeller2'],
            propeller3=data['propeller3'],
            propeller4=data['propeller4'],
            propeller5=data['propeller5']
        )
        new_TempWall_data = TempWallData(
            date=date_time,
            group=data['group'],
            propeller1=data['propeller1'],
            propeller2=data['propeller2'],
            propeller3=data['propeller3'],
            propeller4=data['propeller4'],
            propeller5=data['propeller5']
        )

        if total_sum >= 0.2:
            # Guardar el objeto en la base de datos
            db.session.add(new_wall_data)
            db.session.add(new_TempWall_data)

            # Actualizar el total del día
            sum_group1 = data['propeller1'] + data['propeller2'] 
            sum_group2 = data['propeller3']
            sum_group3 = data['propeller4'] + data['propeller5']

            update_total_day(today, total_sum, sum_group1, sum_group2, sum_group3)

            # Actualizar el total del mes
            update_total_month(month, total_sum)

            # Actualizar el total general
            update_total_all(total_sum)

            return jsonify(new_wall_data.to_json())
        else:
            return jsonify({'message': 'Data not saved. Total sum is less than 0.2'})

@app.route(BASE_URL + "/update", methods=["POST"])
def update_status():
    try:
        data = request.get_json()
        if "status" not in data:
            return jsonify({"error": "Missing 'status' field"}), 400
        
        new_status = int(data["status"])
        if new_status not in [0, 1]:
            return jsonify({"error": "Invalid status value. Must be 0 or 1"}), 400

        # Guardar el nuevo estado con timestamp actual
        new_log = SystemStatus(status=new_status)
        db.session.add(new_log)
        db.session.commit()

        return jsonify({
            "message": "New status recorded",
            "status": new_status,
            "lastUpdate": new_log.last_update.strftime('%Y-%m-%d %H:%M:%S')
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def monitor_xiao_status():
    while True:
        time.sleep(60)  # Revisar cada 1 minuto
        with app.app_context():
            latest_status = SystemStatus.query.order_by(SystemStatus.last_update.desc()).first()
            
            if latest_status:
                now = datetime.now(pytz.utc)  # Ahora en UTC
                last_update = latest_status.last_update.replace(tzinfo=pytz.utc)  # Asegurar que tenga UTC

                print(f"Última actualización recibida: {last_update} | Hora actual: {now}")

                # Si han pasado más de 3 minutos sin recibir un 1, guardar un 0
                if latest_status.status == 1 and (now - last_update) > timedelta(minutes=3):
                    print("⚠️ No se ha recibido señal de la Xiao en más de 3 minutos. Registrando estado 0...")
                    
                    new_log = SystemStatus(status=0)
                    db.session.add(new_log)
                    db.session.commit()
                    
                    print("✅ Estado cambiado a 0 por inactividad de la Xiao.")

# ---GET----------------------------------------------------------------

# GETs | WallData

@app.route(BASE_URL + "/statusHistory", methods=["GET"])
def get_status_history():
    logs = SystemStatus.query.order_by(SystemStatus.last_update.desc()).all()

    history = [
        {
            "id": log.id,
            "status": log.status,
            "lastUpdate": log.last_update.replace(tzinfo=pytz.utc).astimezone(mexico_tz).strftime('%Y-%m-%d %H:%M:%S')
        }
        for log in logs
    ]

    return jsonify(history), 200



@app.route(BASE_URL + "/status", methods=["GET"])
def get_status():
    system_status = SystemStatus.query.order_by(SystemStatus.last_update.desc()).first()
    
    if not system_status:
        return jsonify({"status": 0, "message": "No status found"}), 404

    last_update_mx = system_status.last_update.replace(tzinfo=pytz.utc).astimezone(mexico_tz)
    formatted_last_update = last_update_mx.strftime('%Y-%m-%d %H:%M:%S')

    return jsonify({
        "status": system_status.status,
        "lastUpdate": formatted_last_update
    }), 200



@app.route(BASE_URL + "/resetStatusHistory", methods=["DELETE"])
def reset_status_history():
    try:
        db.session.query(SystemStatus).delete()
        db.session.commit()
        return jsonify({"message": "Status history deleted"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500





@app.route(BASE_URL + '/readTempLatest/<number>', methods=['GET'])
def readTempLatest(number):
    latest_data = TempWallData.query.filter_by(group=number).order_by(TempWallData.id.desc()).first()
    return jsonify(latest_data.to_json())

# -----------------------------------------------------------------------

@app.route(BASE_URL + '/readLatest', methods=['GET'])
def readLatest():
    latest_data = WallData.query.order_by(WallData.id.desc()).first()
    return jsonify(latest_data.to_json())
# -----------------------------------------------------------------------
@app.route(BASE_URL + '/readAll', methods=['GET'])
def readAll():
    all_data = WallData.query.all()
    return jsonify([data.to_json() for data in all_data])
# -----------------------------------------------------------------------
@app.route(BASE_URL + '/getAllHours', methods=['GET'])
def get_all_hours():
    date_str = request.args.get('date')
    if not date_str:
        date = datetime.now(mexico_tz).date()
    else:
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    all_data = WallData.query.filter(cast(WallData.date, Date) == date).all()

    hourly_totals = {hour: 0 for hour in range(24)}

    for data in all_data:
        hour = data.date.hour
        total = ((data.propeller1 ** 2/216 * 1000) + (data.propeller2 ** 2/216 * 1000) + (data.propeller3 ** 2/216 * 1000) + (data.propeller4 ** 2/216 * 1000) + (data.propeller5 ** 2/216 * 1000))
        hourly_totals[hour] += total

    return jsonify(hourly_totals)

# -----------------------------------------------------------------------
@app.route(BASE_URL + '/getAllMinutes', methods=['GET'])
def get_all_minutes():
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'Date parameter is required'}), 400

    try:
        date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD HH:MM:SS'}), 400


    all_data = WallData.query.filter(
        WallData.date >= date.replace(minute=0, second=0, microsecond=0),
        WallData.date < date.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
    ).all()
    
    print(all_data)
    minute_totals = {minute: {
        'propeller1': 0,
        'propeller2': 0,
        'propeller3': 0,
        'propeller4': 0,
        'propeller5': 0,
        'total': 0
    } for minute in range(60)}

    print(all_data)
    for data in all_data:
        minute = data.date.minute
        minute_totals[minute]['propeller1'] += data.propeller1 ** 2/216 * 1000
        minute_totals[minute]['propeller2'] += data.propeller2 ** 2/216 * 1000
        minute_totals[minute]['propeller3'] += data.propeller3 ** 2/216 * 1000
        minute_totals[minute]['propeller4'] += data.propeller4 ** 2/216 * 1000
        minute_totals[minute]['propeller5'] += data.propeller5 ** 2/216 * 1000
        minute_totals[minute]['total'] += ((data.propeller1 ** 2/216 * 1000) + (data.propeller2 ** 2/216 * 1000) + (data.propeller3 ** 2/216 * 1000) + (data.propeller4 ** 2/216 * 1000) + (data.propeller5 ** 2/216 * 1000))

    return jsonify(minute_totals)
# -----------------------------------------------------------------------
@app.route(BASE_URL + '/getHourByNumber/<number>', methods=['GET'])
def get_hour_by_number(number):

    today = datetime.now(mexico_tz).date()
    all_data = WallData.query.filter(cast(WallData.date, Date) == today).all()

    total = 0

    for data in all_data:
        if data.date.hour == int(number):
            total += data.propeller1 + data.propeller2 + data.propeller3 + data.propeller4 + data.propeller5

    return jsonify({'hour': number, 'total': total})

# -----------------------------------------------------------------------
@app.route(BASE_URL + '/get_totals', methods=['GET'])
def get_totals():
    # Realiza una consulta para sumar los propellers por grupo
    results = (
        db.session.query(
            WallData.group,
            func.sum(
                WallData.propeller1 +
                WallData.propeller2 +
                WallData.propeller3 +
                WallData.propeller4 +
                WallData.propeller5
            ).label('total')
        )
        .group_by(WallData.group)
        .all()
    )
    
    # Convierte los resultados a un diccionario
    totals = {f'group{row[0]}': row[1] for row in results}
    
    return jsonify(totals)
#- Fin de GET para WallData-----------------------------------------------

# GETs | TotalDay -------------------------------------------------------

@app.route(BASE_URL + '/readAllDays', methods=['GET'])
def readAllDays():
    all_data = TotalDay.query.all()
    return jsonify([data.to_json() for data in all_data])

# -----------------------------------------------------------------------

@app.route(BASE_URL + '/getCurrentDay', methods=['GET'])
def get_current_day():
    today = datetime.now(mexico_tz).date()
    today_object = TotalDay.query.filter_by(date=today).first()



    if today_object is None:
        return jsonify({'total': 0})
    else:
        return jsonify(today_object.to_json())

# -----------------------------------------------------------------------
@app.route(BASE_URL + '/read30days', methods=['GET'])
def read30days():

    # Hacer un diccionario del 1 al 30 que tenga el total de cada día
    today = datetime.now(mexico_tz).date()
    thirty_days_ago = today - timedelta(days=30)
    all_data = TotalDay.query.filter(TotalDay.date >= thirty_days_ago, TotalDay.date <= today).all()

    # Crear un diccionario con los últimos 30 días, inicializando en 0
    day_totals = { (thirty_days_ago + timedelta(days=i)).strftime('%d'): 0 for i in range(31) }

    # Actualizar el diccionario con los valores reales
    for day in all_data:
        day_totals[day.date.strftime('%d')] = day.total

    return jsonify(day_totals)
# -----------------------------------------------------------------------

@app.route(BASE_URL + '/getWeek', methods=['GET'])
def get_week():
    today = datetime.now(mexico_tz).date()
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    week_data = TotalDay.query.filter(TotalDay.date >= week_start, TotalDay.date <= week_end).all()

    week_totals = {day.date.strftime('%A, %Y-%m-%d'): (day.total ** 2/216 * 1000) for day in week_data}
    total_week = sum(day.total for day in week_data)

    return jsonify({'week_totals': week_totals, 'total_week': total_week})

# -----------------------------------------------------------------------

@app.route(BASE_URL + '/getDayByNumber/<number>', methods=['GET'])
def get_day_by_number(number):

    today = datetime.now(mexico_tz).date()
    all_data = TotalDay.query.all()

    total = 0

    for data in all_data:
        if data.date.day == int(number):
            total += data.total

    return jsonify({'day': number, 'total': total})

#- Fin de GET para TotalDay -----------------------------------------------

# GETs | TotalMonth -----------------------------------------------------

@app.route(BASE_URL + '/getCurrentMonth', methods=['GET'])
def get_current_month():
    today = datetime.now(mexico_tz).date()
    month_start = today.replace(day=1)
    month_object = TotalMonth.query.filter_by(date=month_start).first()

    if month_object is None:
        return jsonify({'total': 0})
    else:
        return jsonify(month_object.to_json())
    
# -----------------------------------------------------------------------
@app.route(BASE_URL + '/readAllMonths', methods=['GET'])
def readAllMonths():
    all_data = TotalMonth.query.all()

    #Crear un diccionario de meses del 1 al 12 que tenga el total de cada mes
    month_totals = {month: 0 for month in range(1, 13)}

    for data in all_data:
        month = data.date.month
        month_totals[month] += data.total

    return jsonify(month_totals)

# -----------------------------------------------------------------------
@app.route(BASE_URL + '/getMonthsObjects', methods=['GET'])
def get_months_objects():
    all_data = TotalMonth.query.all()
    return jsonify([data.to_json() for data in all_data])

#- Fin de GET para TotalMonth --------------------------------------------

# GETs | TotalAll -------------------------------------------------------
@app.route(BASE_URL + '/getTotal', methods=['GET'])
def get_total():
    total_object = TotalAll.query.first()

    if total_object is None:
        return jsonify({'total': 0})
    else:
        return jsonify(total_object.to_json())

# -----------------------------------------------------------------------



# ---DELETE-------------------------------------------------------------
@app.route(BASE_URL + '/resetAll', methods=['DELETE'])
def resetAll():
    db.session.query(WallData).delete()
    db.session.query(TotalDay).delete()
    db.session.query(TotalMonth).delete()
    db.session.query(TotalAll).delete()
    db.session.commit()
    return jsonify({'message': 'All data has been deleted'})
# -----------------------------------------------------------------------
@app.route(BASE_URL + '/resetTempWallData', methods=['DELETE'])
def resetTempWallData():
    db.session.query(TempWallData).delete()
    db.session.commit()
    return jsonify({'message': 'All data has been deleted'})
# -----------------------------------------------------------------------
@app.route(BASE_URL + '/deleteAllZeros', methods=['DELETE'])
def deleteAllZeros():
    db.session.query(WallData).filter(WallData.propeller1 == 0, WallData.propeller2 == 0, WallData.propeller3 == 0, WallData.propeller4 == 0, WallData.propeller5 == 0).delete()
    db.session.commit()
    return jsonify({'message': 'All zeros have been deleted'})
# -----------------------------------------------------------------------

@app.route(BASE_URL + '/deleteLastStatus', methods=['DELETE'])
def delete_last_status():
    try:
        last_entry = SystemStatus.query.order_by(SystemStatus.id.desc()).first()
        if last_entry:
            db.session.delete(last_entry)
            db.session.commit()
            return jsonify({"message": "Last status entry deleted", "deleted_entry": last_entry.to_json()}), 200
        else:
            return jsonify({"message": "No status entries found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
# -----------------------------------------------------------------------

@app.route(BASE_URL + '/deleteLastWallData', methods=['DELETE'])
def delete_last_wall_data():
    try:
        last_entry = WallData.query.order_by(WallData.id.desc()).first()
        if last_entry:
            db.session.delete(last_entry)
            db.session.commit()
            return jsonify({"message": "Last WallData entry deleted", "deleted_entry": last_entry.to_json()}), 200
        else:
            return jsonify({"message": "No WallData entries found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

@app.route(BASE_URL + '/deleteRangeWallData', methods=['DELETE'])
def delete_range_wall_data():
    try:
        data = request.get_json()
        start_id = data.get("start_id")
        end_id = data.get("end_id")

        if start_id is None or end_id is None:
            return jsonify({"error": "Missing 'start_id' or 'end_id' in request"}), 400

        # Eliminar el rango especificado
        deleted = WallData.query.filter(WallData.id >= start_id, WallData.id <= end_id).delete(synchronize_session=False)
        db.session.commit()

        return jsonify({
            "message": f"{deleted} entries deleted from WallData",
            "range": f"{start_id} to {end_id}"
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route(BASE_URL + '/updateStatusRange', methods=['PUT'])
def update_status_range():
    try:
        data = request.get_json()
        start_id = data.get("start_id")
        end_id = data.get("end_id")

        if start_id is None or end_id is None:
            return jsonify({"error": "Missing 'start_id' or 'end_id'"}), 400

        # Filtrar solo los registros con status = 0 dentro del rango
        entries = SystemStatus.query.filter(
            SystemStatus.id >= start_id,
            SystemStatus.id <= end_id,
            SystemStatus.status == 0
        ).all()

        updated_ids = []

        for entry in entries:
            entry.status = 1
            updated_ids.append(entry.id)
            # No se actualiza last_update

        db.session.commit()

        return jsonify({
            "message": f"{len(updated_ids)} entries updated from 0 to 1 (timestamp preserved)",
            "updated_ids": updated_ids
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# Ejecutar la función en un hilo separado para no bloquear la API
threading.Thread(target=monitor_xiao_status, daemon=True).start()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("Tables created")
    app.run(debug=False)

# -----------------------------------------------------------------------
# FIN DE | METODOS HTTP
# -----------------------------------------------------------------------