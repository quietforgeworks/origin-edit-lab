// This observes actual imported QObject signals and public column APIs.
// It has no Origin-file parser and supplies no replacement numerical data.
#include <QSignalSpy>
#include <QPointF>
#include <QVector>
#include <QJsonArray>
#include <QJsonObject>
#include <QJsonDocument>
static QObject* observedCurve=nullptr;
static QSignalSpy* pointSpy=nullptr;
static QString bits(double value){uint64_t b;memcpy(&b,&value,8);return QString("%1").arg(b,16,16,QChar('0'));}
static QObject* findCurve(QAbstractItemModel*m,QModelIndex p={},int depth=0){
 if(depth>9)return nullptr;
 for(int r=0;r<m->rowCount(p);r++){
  auto idx=m->index(r,0,p);
  if(m->data(m->index(r,1,p)).toString()=="Plot") {
   auto*o=static_cast<QObject*>(idx.internalPointer());
   if(o && QString(o->metaObject()->className())=="XYCurve")return o;
  }
  auto c=m->index(0,0,idx);if(c.isValid()&&c.parent()==idx)if(auto*o=findCurve(m,idx,depth+1))return o;
 }return nullptr;
}
static void watchCurve(){
 for(auto*w:QApplication::allWidgets())if(w->isVisible())if(auto*v=qobject_cast<QTreeView*>(w))if(v->model())if(auto*o=findCurve(v->model())){
  observedCurve=o;
  for(int k=0;k<o->metaObject()->methodCount();k++){
   auto m=o->metaObject()->method(k);
   if(m.methodType()==QMetaMethod::Signal && m.name()=="pointsUpdated") {pointSpy=new QSignalSpy(o,m);fprintf(stderr,"Observed %s signal %s valid=%d\n",o->metaObject()->className(),m.methodSignature().constData(),pointSpy->isValid());return;}
  }return;
 }
 fprintf(stderr,"No imported XYCurve object available for signal observation\n");
}
static void recordCurve(){
 QJsonObject out;out["method"]="Actual imported XYCurve pointers, public Column::valueAt/rowCount and AbstractColumn::isValid/isMasked; passive QSignalSpy";
 out["curve_found"]=observedCurve!=nullptr;out["signal_spy_valid"]=pointSpy&&pointSpy->isValid();
 void*lib=dlopen(qEnvironmentVariable("OBSERVER_BUNDLED_LIB").toUtf8().constData(),RTLD_LAZY|RTLD_LOCAL);
 auto xcol=(const void*(*)(const void*))dlsym(lib,"_ZNK7XYCurve7xColumnEv");
 auto ycol=(const void*(*)(const void*))dlsym(lib,"_ZNK7XYCurve7yColumnEv");
 auto rowCount=(int(*)(const void*))dlsym(lib,"_ZNK6Column8rowCountEv");
 auto valueAt=(double(*)(const void*,int))dlsym(lib,"_ZNK6Column7valueAtEi");
 auto valid=(bool(*)(const void*,int))dlsym(lib,"_ZNK14AbstractColumn7isValidEi");
 auto masked=(bool(*)(const void*,int))dlsym(lib,"_ZNK14AbstractColumn8isMaskedEi");
 if(observedCurve&&xcol&&ycol&&rowCount&&valueAt&&valid&&masked){
  auto*x=xcol(observedCurve);auto*y=ycol(observedCurve);out["x_bound"]=x!=nullptr;out["y_bound"]=y!=nullptr;
  if(x&&y){out["x_allocated_rows"]=rowCount(x);out["y_allocated_rows"]=rowCount(y);QJsonArray rows;
   for(int r=0;r<qMin(rowCount(x),rowCount(y));r++){
    QJsonObject cell;cell["row"]=r;cell["x_bits"]=bits(valueAt(x,r));cell["y_bits"]=bits(valueAt(y,r));
    cell["x_valid"]=valid(x,r);cell["y_valid"]=valid(y,r);cell["x_masked"]=masked(x,r);cell["y_masked"]=masked(y,r);rows.append(cell);
   }out["rows"]=rows;
  }
 }
 QJsonArray emissions;
 if(pointSpy)for(const auto& args:*pointSpy){QJsonObject e;e["start_index"]=args.at(1).toInt();e["end_index"]=args.at(2).toInt();auto points=args.at(3).value<QList<QPointF>>();e["logical_point_count"]=points.size();QJsonArray pp;for(const auto&p:points){QJsonArray a;a.append(bits(p.x()));a.append(bits(p.y()));pp.append(a);}e["logical_points_binary64"]=pp;emissions.append(e);}
 out["point_signal_emissions"]=emissions;
 QFile f(qEnvironmentVariable("OBSERVER_OUT")+"/curve-observation.json");f.open(QIODevice::WriteOnly);f.write(QJsonDocument(out).toJson());
}
